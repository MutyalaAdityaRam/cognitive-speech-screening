<?php
declare(strict_types=1);

require_once __DIR__ . '/../config/database.php';
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

function proxy_upload_report(string $filePath, int $userId, string $userName): array
{
    $aiUrl = ai_service_url();
    $curl = curl_init($aiUrl . '/upload-report');
    curl_setopt_array($curl, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => [
            'user_id' => (string)$userId,
            'user_name' => $userName,
            'file' => new CURLFile($filePath, mime_content_type($filePath) ?: 'application/octet-stream', basename($filePath)),
        ],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 300,
    ]);
    $body = curl_exec($curl);
    $error = curl_error($curl);
    $status = curl_getinfo($curl, CURLINFO_HTTP_CODE);
    curl_close($curl);
    if ($body === false) {
        throw new RuntimeException($error ?: 'AI report upload failed');
    }
    $json = json_decode($body, true);
    if (!is_array($json)) {
        throw new RuntimeException('AI service returned non-JSON response: ' . substr(trim((string)$body), 0, 300));
    }
    if ($status >= 400) {
        throw new RuntimeException((string)($json['detail'] ?? $json['message'] ?? ('AI service returned HTTP ' . $status)));
    }
    return $json;
}

try {
    if (!isset($_FILES['report'])) {
        echo json_encode(['error' => 'Report file is required']);
        http_response_code(422);
        exit;
    }
    $userId = (int)($_POST['user_id'] ?? 0);
    if ($userId <= 0) {
        echo json_encode(['error' => 'Valid user_id is required']);
        http_response_code(422);
        exit;
    }
    $nameStmt = db()->prepare('SELECT name FROM users WHERE id = ? LIMIT 1');
    $nameStmt->execute([$userId]);
    $user = $nameStmt->fetch();
    $userName = (string)($user['name'] ?? '');
    $uploadDir = __DIR__ . '/../storage/uploaded_reports/';
    if (!is_dir($uploadDir)) {
        mkdir($uploadDir, 0777, true);
    }
    $safeName = preg_replace('/[^a-zA-Z0-9._-]/', '_', basename($_FILES['report']['name']));
    $destination = $uploadDir . uniqid('', true) . '_' . $safeName;
    move_uploaded_file($_FILES['report']['tmp_name'], $destination);

    $ai = proxy_upload_report($destination, $userId, $userName);
    $stmt = db()->prepare('INSERT INTO uploaded_reports (user_id, file_path, extracted_text) VALUES (?, ?, ?)');
    $stmt->execute([$userId, $destination, $ai['extracted_text'] ?? '']);
    $uploadedId = (int)db()->lastInsertId();

    echo json_encode([
        'uploaded_report_id' => $uploadedId,
        'file_path' => $destination,
        'extracted_text' => $ai['extracted_text'] ?? '',
        'analysis' => $ai['analysis'] ?? '',
    ]);
} catch (Throwable $e) {
    echo json_encode(['error' => $e->getMessage()]);
    http_response_code(500);
}
