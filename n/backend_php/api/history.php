<?php
declare(strict_types=1);

require_once __DIR__ . '/../config/database.php';

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

if (!in_array($_SERVER['REQUEST_METHOD'], ['GET', 'POST'], true)) {
    echo json_encode(['error' => 'Method not allowed']);
    http_response_code(405);
    exit;
}

try {
    $input = json_decode(file_get_contents('php://input'), true) ?: $_POST;
    $userId = (int)(($_SERVER['REQUEST_METHOD'] === 'POST' ? ($input['user_id'] ?? 0) : ($_GET['user_id'] ?? 0)));
    $stmt = db()->prepare(
        'SELECT r.id, s.prediction, s.final_probability, s.confidence, s.transcript, r.report_path, r.report_text, r.created_at
         FROM reports r
         INNER JOIN sessions s ON s.id = r.session_id
         WHERE s.user_id = ?
         ORDER BY r.created_at DESC'
    );
    $stmt->execute([$userId]);
    echo json_encode(['reports' => $stmt->fetchAll()]);
} catch (Throwable $e) {
    echo json_encode(['error' => $e->getMessage()]);
    http_response_code(500);
}
