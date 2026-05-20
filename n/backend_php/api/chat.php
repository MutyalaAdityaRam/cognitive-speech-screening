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

function proxy_chat(array $payload): array
{
    $aiUrl = ai_service_url();
    $fullUrl = $aiUrl . '/chat';
    error_log("Calling chat service at: " . $fullUrl);
    
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

function save_chat_message(int $sessionId, string $sender, string $message): int
{
    $stmt = db()->prepare('INSERT INTO chat_messages (session_id, sender, message) VALUES (?, ?, ?)');
    $stmt->execute([$sessionId, $sender, $message]);
    return (int)db()->lastInsertId();
}

try {
    $startTime = microtime(true);
    error_log("Chat.php started at " . date('Y-m-d H:i:s'));

    $input = json_decode(file_get_contents('php://input'), true) ?: $_POST;
    $userId = (int)($input['user_id'] ?? 0);
    $question = trim((string)($input['question'] ?? ''));
    $context = $input['context'] ?? null;

    error_log("Chat User ID: $userId, Question: $question");

    if ($userId <= 0) {
        $name = $input['name'] ?? 'Anonymous';
        $email = $input['email'] ?? 'anonymous@example.com';
        $stmt = db()->prepare('INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)');
        $stmt->execute([$name, $email, '']);
        $userId = (int)db()->lastInsertId();
    }

    if (!is_array($context)) {
        $context = [];
    }
    if (empty($context['user_name'])) {
        $nameStmt = db()->prepare('SELECT name FROM users WHERE id = ? LIMIT 1');
        $nameStmt->execute([$userId]);
        $user = $nameStmt->fetch();
        if ($user && !empty($user['name'])) {
            $context['user_name'] = $user['name'];
        }
    }

    $chatSessionStmt = db()->prepare('INSERT INTO chat_sessions (user_id) VALUES (?)');
    $chatSessionStmt->execute([$userId]);
    $chatSessionId = (int)db()->lastInsertId();

    save_chat_message($chatSessionId, 'user', $question);

    $t1 = microtime(true);
    $aiResponse = proxy_chat(['question' => $question, 'context' => $context]);
    error_log("Proxy chat took: " . round(microtime(true) - $t1, 2) . "s");
    
    $answer = $aiResponse['answer'];

    save_chat_message($chatSessionId, 'system', $answer);

    $response = [
        'chat_session_id' => $chatSessionId,
        'user_id' => $userId,
        'question' => $question,
        'answer' => $answer,
    ];

    error_log("Chat.php total time: " . round(microtime(true) - $startTime, 2) . "s");
    error_log("Chat response: " . json_encode($response));

    echo json_encode($response);
} catch (Throwable $e) {
    error_log("Error in chat.php: " . $e->getMessage() . " in " . $e->getFile() . ":" . $e->getLine());
    echo json_encode(['error' => $e->getMessage()]);
    http_response_code(500);
}
