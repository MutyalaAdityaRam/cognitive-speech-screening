<?php
declare(strict_types=1);

require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../config/ai_service.php';

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

$route = $_GET['route'] ?? 'health';

function json_response(array $payload, int $status = 200): void
{
    http_response_code($status);
    echo json_encode($payload, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    exit;
}

function ai_base_url(): string
{
    return ai_service_url();
}

function proxy_file(string $endpoint, string $filePath): array
{
    $curl = curl_init(ai_base_url() . $endpoint);
    $payload = [
        'file' => new CURLFile($filePath, mime_content_type($filePath) ?: 'application/octet-stream', basename($filePath)),
    ];
    curl_setopt_array($curl, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $payload,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 180,
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
    $curl = curl_init(ai_base_url() . '/report');
    curl_setopt_array($curl, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode($payload, JSON_THROW_ON_ERROR),
        CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 180,
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

function proxy_chat(array $payload): array
{
    $curl = curl_init(ai_base_url() . '/chat');
    curl_setopt_array($curl, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode($payload, JSON_THROW_ON_ERROR),
        CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 120,
    ]);
    $body = curl_exec($curl);
    $error = curl_error($curl);
    $status = curl_getinfo($curl, CURLINFO_HTTP_CODE);
    curl_close($curl);
    if ($body === false) {
        throw new RuntimeException($error ?: 'AI chat request failed');
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
        throw new InvalidArgumentException('name and email are required');
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

function register_user(array $payload): int
{
    $name = trim((string)($payload['name'] ?? ''));
    $email = trim((string)($payload['email'] ?? ''));
    $password = (string)($payload['password'] ?? '');
    $age = $payload['age'] ?? null;

    if ($name === '' || $email === '' || $password === '') {
        throw new InvalidArgumentException('name, email, and password are required');
    }

    if (strlen($password) < 6) {
        throw new InvalidArgumentException('password must be at least 6 characters');
    }

    $stmt = db()->prepare('SELECT id FROM users WHERE email = ? LIMIT 1');
    $stmt->execute([$email]);
    if ($stmt->fetch()) {
        throw new InvalidArgumentException('email already registered');
    }

    $passwordHash = password_hash($password, PASSWORD_DEFAULT);
    $insert = db()->prepare('INSERT INTO users (name, email, password_hash, age) VALUES (?, ?, ?, ?)');
    $insert->execute([$name, $email, $passwordHash, $age !== null ? (int)$age : null]);
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

    return ['session_id' => $sessionId, 'report_id' => (int)db()->lastInsertId()];
}

function save_chat_message(int $sessionId, string $sender, string $message): int
{
    $stmt = db()->prepare('INSERT INTO chat_messages (session_id, sender, message) VALUES (?, ?, ?)');
    $stmt->execute([$sessionId, $sender, $message]);
    return (int)db()->lastInsertId();
}

try {
    if ($route === 'health') {
        json_response(['status' => 'ok', 'service' => 'php-gateway']);
    }

    if ($route === 'register' && $_SERVER['REQUEST_METHOD'] === 'POST') {
        $payload = json_decode(file_get_contents('php://input'), true) ?: $_POST;
        $userId = register_user($payload);
        json_response(['user_id' => $userId, 'message' => 'user registered successfully'], 201);
    }

    if ($route === 'login' && $_SERVER['REQUEST_METHOD'] === 'POST') {
        $payload = json_decode(file_get_contents('php://input'), true) ?: $_POST;
        $email = trim((string)($payload['email'] ?? ''));
        $password = (string)($payload['password'] ?? '');

        if ($email === '' || $password === '') {
            json_response(['error' => 'email and password are required'], 422);
        }

        $stmt = db()->prepare('SELECT id, password_hash FROM users WHERE email = ? LIMIT 1');
        $stmt->execute([$email]);
        $user = $stmt->fetch();

        if (!$user || !password_verify($password, $user['password_hash'])) {
            json_response(['error' => 'invalid email or password'], 401);
        }

        json_response(['user_id' => (int)$user['id'], 'message' => 'login successful'], 200);
    }

    if ($route === 'predict_audio' && $_SERVER['REQUEST_METHOD'] === 'POST') {
        if (!isset($_FILES['audio'])) {
            json_response(['error' => 'audio file is required'], 422);
        }

        $userId = (int)($_POST['user_id'] ?? 0);
        if ($userId <= 0) {
            $userId = ensure_user($_POST + ['name' => $_POST['name'] ?? 'Anonymous', 'email' => $_POST['email'] ?? 'anonymous@example.com']);
        }
        $filePath = $_FILES['audio']['tmp_name'];

        $transcription = proxy_file('/transcribe', $filePath);
        if (($transcription['status'] ?? '') === 'needs_restart') {
            json_response($transcription);
        }

        $prediction = proxy_file('/predict', $filePath);
        $report = proxy_report([
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

        $combined = array_merge($prediction, $transcription, $report);
        $saved = save_session_and_report($userId, $_FILES['audio']['name'], $combined);
        $combined['user_id'] = $userId;
        $combined['session_id'] = $saved['session_id'];
        $combined['report_id'] = $saved['report_id'];
        json_response($combined);
    }

    if ($route === 'reports' && $_SERVER['REQUEST_METHOD'] === 'GET') {
        $userId = (int)($_GET['user_id'] ?? 0);
        $stmt = db()->prepare(
            'SELECT r.id, s.prediction, s.final_probability, s.confidence, r.created_at
             FROM reports r
             INNER JOIN sessions s ON s.id = r.session_id
             WHERE s.user_id = ?
             ORDER BY r.created_at DESC'
        );
        $stmt->execute([$userId]);
        json_response(['reports' => $stmt->fetchAll()]);
    }

    if ($route === 'report_detail' && $_SERVER['REQUEST_METHOD'] === 'GET') {
        $id = (int)($_GET['id'] ?? 0);
        $stmt = db()->prepare(
            'SELECT r.id, s.user_id, s.prediction, s.final_probability, s.confidence, r.report_text, r.created_at
             FROM reports r
             INNER JOIN sessions s ON s.id = r.session_id
             WHERE r.id = ?'
        );
        $stmt->execute([$id]);
        json_response(['report' => $stmt->fetch()]);
    }

    if ($route === 'chat' && $_SERVER['REQUEST_METHOD'] === 'POST') {
        $payload = json_decode(file_get_contents('php://input'), true) ?: $_POST;
        $userId = (int)($payload['user_id'] ?? 0);
        $question = trim((string)($payload['question'] ?? ''));
        $context = $payload['context'] ?? null;
        
        if ($userId <= 0) {
            $userId = ensure_user([
                'name' => $payload['name'] ?? 'Anonymous',
                'email' => $payload['email'] ?? 'anonymous@example.com',
            ]);
        }
        
        $chatSessionStmt = db()->prepare('INSERT INTO chat_sessions (user_id) VALUES (?)');
        $chatSessionStmt->execute([$userId]);
        $chatSessionId = (int)db()->lastInsertId();
        
        save_chat_message($chatSessionId, 'user', $question);
        
        $aiResponse = proxy_chat(['question' => $question, 'context' => $context]);
        $answer = $aiResponse['answer'];
        
        save_chat_message($chatSessionId, 'system', $answer);
        
        json_response([
            'chat_session_id' => $chatSessionId,
            'user_id' => $userId,
            'question' => $question,
            'answer' => $answer,
        ]);
    }

    if ($route === 'chat_history' && $_SERVER['REQUEST_METHOD'] === 'GET') {
        $chatSessionId = (int)($_GET['chat_session_id'] ?? 0);
        $stmt = db()->prepare(
            'SELECT id, sender, message, created_at
             FROM chat_messages
             WHERE session_id = ?
             ORDER BY created_at ASC'
        );
        $stmt->execute([$chatSessionId]);
        json_response(['messages' => $stmt->fetchAll()]);
    }

    json_response(['error' => 'route not found'], 404);
} catch (Throwable $e) {
    json_response(['error' => $e->getMessage()], 500);
}
