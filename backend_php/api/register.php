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
    $name = trim((string)($input['name'] ?? ''));
    $email = trim((string)($input['email'] ?? ''));
    $password = (string)($input['password'] ?? '');
    $age = $input['age'] ?? null;

    if ($name === '' || $email === '' || $password === '') {
        echo json_encode(['error' => 'Name, email, and password are required']);
        http_response_code(422);
        exit;
    }

    if (strlen($password) < 6) {
        echo json_encode(['error' => 'Password must be at least 6 characters']);
        http_response_code(422);
        exit;
    }

    $stmt = db()->prepare('SELECT id FROM users WHERE email = ? LIMIT 1');
    $stmt->execute([$email]);
    if ($stmt->fetch()) {
        echo json_encode(['error' => 'Email already registered']);
        http_response_code(422);
        exit;
    }

    $passwordHash = password_hash($password, PASSWORD_DEFAULT);
    $insert = db()->prepare('INSERT INTO users (name, email, password_hash, age) VALUES (?, ?, ?, ?)');
    $insert->execute([$name, $email, $passwordHash, $age !== null ? (int)$age : null]);
    $userId = (int)db()->lastInsertId();

    echo json_encode(['user_id' => $userId, 'name' => $name, 'message' => 'Account created successfully']);
    http_response_code(201);
} catch (Throwable $e) {
    echo json_encode(['error' => $e->getMessage()]);
    http_response_code(500);
}
