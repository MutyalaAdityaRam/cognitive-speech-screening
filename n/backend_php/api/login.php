<?php
declare(strict_types=1);

require_once __DIR__ . '/../config/database.php';

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

try {
    $input = json_decode(file_get_contents('php://input'), true) ?: $_POST;
    $email = trim((string)($input['email'] ?? ''));
    $password = (string)($input['password'] ?? '');

    if ($email === '' || $password === '') {
        echo json_encode(['error' => 'Email and password are required']);
        http_response_code(422);
        exit;
    }

    $stmt = db()->prepare('SELECT id, name, password_hash FROM users WHERE email = ? LIMIT 1');
    $stmt->execute([$email]);
    $user = $stmt->fetch();

    if (!$user || !password_verify($password, $user['password_hash'])) {
        echo json_encode(['error' => 'Invalid email or password']);
        http_response_code(401);
        exit;
    }

    echo json_encode(['user_id' => (int)$user['id'], 'name' => $user['name'], 'message' => 'Login successful']);
} catch (Throwable $e) {
    echo json_encode(['error' => $e->getMessage()]);
    http_response_code(500);
}
