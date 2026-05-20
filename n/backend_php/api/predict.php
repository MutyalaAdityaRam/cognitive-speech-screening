<?php
declare(strict_types=1);

require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../config/report_files.php';
require_once __DIR__ . '/../config/ai_service.php';

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    echo json_encode(['error' => 'Method not allowed']);
    http_response_code(405);
    exit;
}

function proxy_file(string $endpoint, string $filePath): array
{
    $curl = curl_init(ai_service_url() . $endpoint);
    $payload = [
        'file' => new CURLFile($filePath, mime_content_type($filePath) ?: 'audio/wav', basename($filePath)),
    ];
    curl_setopt_array($curl, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $payload,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 300,
    ]);
    $body = curl_exec($curl);
    $error = curl_error($curl);
    $status = curl_getinfo($curl, CURLINFO_HTTP_CODE);
    curl_close($curl);
    if ($body === false) {
        throw new RuntimeException($error ?: 'AI service request failed');
    }
    $json = json_decode($body, true);
    if (!is_array($json)) {
        $snippet = substr(trim((string)$body), 0, 300);
        throw new RuntimeException('AI service returned non-JSON response: ' . $snippet);
    }
    if ($status >= 400) {
        $message = $json['detail'] ?? $json['message'] ?? ('AI service returned HTTP ' . $status);
        throw new RuntimeException((string)$message);
    }
    return $json;
}

function proxy_report(array $payload): array
{
    $aiUrl = ai_service_url();
    $fullUrl = $aiUrl . '/generate-report';
    error_log("Calling report service at: " . $fullUrl);
    
    $curl = curl_init($fullUrl);
    curl_setopt_array($curl, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode($payload, JSON_THROW_ON_ERROR),
        CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 300,
    ]);
    $body = curl_exec($curl);
    $error = curl_error($curl);
    $status = curl_getinfo($curl, CURLINFO_HTTP_CODE);
    curl_close($curl);
    if ($body === false) {
        throw new RuntimeException($error ?: 'AI report request failed');
    }
    $json = json_decode($body, true);
    if (!is_array($json)) {
        $snippet = substr(trim((string)$body), 0, 300);
        throw new RuntimeException('AI service returned non-JSON response: ' . $snippet);
    }
    if ($status >= 400) {
        $message = $json['detail'] ?? $json['message'] ?? ('AI service returned HTTP ' . $status);
        throw new RuntimeException((string)$message);
    }
    return $json;
}

function ensure_user(array $payload): int
{
    $name = trim((string)($payload['name'] ?? ''));
    $email = trim((string)($payload['email'] ?? ''));
    $age = $payload['age'] ?? null;

    if ($name === '' || $email === '') {
        $name = 'Anonymous';
        $email = 'anonymous@example.com';
    }

    $stmt = db()->prepare('SELECT id FROM users WHERE email = ? LIMIT 1');
    $stmt->execute([$email]);
    $existing = $stmt->fetch();
    if ($existing) {
        return (int)$existing['id'];
    }

    $insert = db()->prepare('INSERT INTO users (name, email, password_hash, age) VALUES (?, ?, ?, ?)');
    $insert->execute([$name, $email, '', $age !== null ? (int)$age : null]);
    return (int)db()->lastInsertId();
}

function save_session_and_report(int $userId, string $audioPath, array $aiResult): array
{
    $session = db()->prepare(
        'INSERT INTO sessions (user_id, audio_path, transcript, prob_model1, prob_model2, final_probability, prediction, confidence) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
    );
    $session->execute([
        $userId,
        $audioPath,
        $aiResult['transcript'] ?? '',
        $aiResult['prob1'] ?? null,
        $aiResult['prob2'] ?? null,
        $aiResult['final_probability'] ?? null,
        $aiResult['prediction'] ?? '',
        $aiResult['confidence'] ?? null,
    ]);

    $sessionId = (int)db()->lastInsertId();
    $report = db()->prepare('INSERT INTO reports (session_id, report_text) VALUES (?, ?)');
    $report->execute([
        $sessionId,
        $aiResult['final_report'] ?? $aiResult['report_text'] ?? '',
    ]);

    return [
        'session_id' => $sessionId,
        'report_id' => (int)db()->lastInsertId(),
    ];
}

try {
    $startTime = microtime(true);
    error_log("Predict.php started at " . date('Y-m-d H:i:s'));

    if (!isset($_FILES['audio'])) {
        echo json_encode(['error' => 'Audio file is required']);
        http_response_code(422);
        exit;
    }

    $userId = (int)($_POST['user_id'] ?? 0);
    if ($userId <= 0) {
        $userId = ensure_user($_POST);
    }
    $userName = trim((string)($_POST['user_name'] ?? ''));
    if ($userName === '') {
        $nameStmt = db()->prepare('SELECT name FROM users WHERE id = ? LIMIT 1');
        $nameStmt->execute([$userId]);
        $user = $nameStmt->fetch();
        $userName = (string)($user['name'] ?? '');
    }
    
    $uploadDir = __DIR__ . '/../uploads/';
    if (!file_exists($uploadDir)) {
        mkdir($uploadDir, 0777, true);
    }
    $originalName = basename($_FILES['audio']['name']);
    $safeName = preg_replace('/[^a-zA-Z0-9._-]/', '_', $originalName);
    $uniqueName = uniqid() . '_' . $safeName;
    $destination = $uploadDir . $uniqueName;
    move_uploaded_file($_FILES['audio']['tmp_name'], $destination);
    
    $filePath = $destination;
    error_log("User ID: $userId, Saved file: $destination");

    $t1 = microtime(true);
    $transcription = proxy_file('/transcribe', $filePath);
    error_log("Transcribe took: " . round(microtime(true) - $t1, 2) . "s");
    
    if (($transcription['status'] ?? '') === 'needs_restart') {
        echo json_encode($transcription);
        exit;
    }

    $t2 = microtime(true);
    $prediction = proxy_file('/predict', $filePath);
    error_log("Predict took: " . round(microtime(true) - $t2, 2) . "s");

    $t3 = microtime(true);
    $report = proxy_report([
        'user_name' => $userName,
        'prediction' => $prediction['prediction'] ?? null,
        'confidence' => $prediction['confidence'] ?? null,
        'prob1' => $prediction['prob1'] ?? null,
        'prob2' => $prediction['prob2'] ?? null,
        'final_probability' => $prediction['final_probability'] ?? null,
        'transcript' => $prediction['transcript'] ?? ($transcription['transcript'] ?? ''),
        'supporting_observations' => $prediction['supporting_observations'] ?? [],
        'behavioral_indicators' => $prediction['behavioral_indicators'] ?? [],
        'retrieved_knowledge' => $prediction['retrieved_knowledge'] ?? [],
        'rationale' => $prediction['rationale'] ?? '',
        'audio_file_path' => $prediction['audio_file_path'] ?? ($_FILES['audio']['name'] ?? ''),
    ]);
    error_log("Report took: " . round(microtime(true) - $t3, 2) . "s");

    $combined = array_merge($prediction, $transcription, $report);
    $saved = save_session_and_report($userId, $_FILES['audio']['name'], $combined);
    $combined['user_id'] = $userId;
    $combined['session_id'] = $saved['session_id'];
    $combined['report_id'] = $saved['report_id'];
    $combined['download_url'] = 'download-report.php?id=' . $saved['report_id'];
    
    error_log("Total predict.php time: " . round(microtime(true) - $startTime, 2) . "s");
    error_log("Response: " . json_encode($combined));
    
    echo json_encode($combined);
} catch (Throwable $e) {
    error_log("Error in predict.php: " . $e->getMessage() . " in " . $e->getFile() . ":" . $e->getLine());
    echo json_encode(['error' => $e->getMessage()]);
    http_response_code(500);
}
