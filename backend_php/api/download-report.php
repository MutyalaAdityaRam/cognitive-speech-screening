<?php
declare(strict_types=1);

require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../config/report_files.php';

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    http_response_code(405);
    echo 'Method not allowed';
    exit;
}

try {
    $id = (int)($_GET['id'] ?? 0);
    $format = strtolower((string)($_GET['format'] ?? 'pdf'));
    if ($id <= 0 || !in_array($format, ['pdf', 'doc', 'docx'], true)) {
        http_response_code(422);
        echo 'Invalid report request';
        exit;
    }

    $stmt = db()->prepare(
        'SELECT r.id, r.session_id, r.report_path, r.report_text, r.created_at,
                s.user_id, s.transcript, s.prediction, s.confidence, s.final_probability
         FROM reports r
         INNER JOIN sessions s ON s.id = r.session_id
         WHERE r.id = ?
         LIMIT 1'
    );
    $stmt->execute([$id]);
    $row = $stmt->fetch();
    if (!$row) {
        http_response_code(404);
        echo 'Report not found';
        exit;
    }

    $path = (string)($row['report_path'] ?? '');
    $currentExtension = strtolower(pathinfo($path, PATHINFO_EXTENSION));
    if ($path === '' || !is_file($path) || $currentExtension !== $format) {
        $path = save_selected_report_file($id, $format, [
            'risk_level' => $row['prediction'] ?? 'Unknown',
            'confidence' => $row['confidence'] ?? $row['final_probability'] ?? '0',
            'transcript' => $row['transcript'] ?? '',
            'final_report' => $row['report_text'] ?? '',
        ]);
        $update = db()->prepare('UPDATE reports SET report_path = ? WHERE id = ?');
        $update->execute([$path, $id]);
    }

    if ($path === '' || !is_file($path)) {
        http_response_code(404);
        echo 'Report file not found';
        exit;
    }

    $extension = strtolower(pathinfo($path, PATHINFO_EXTENSION));
    header('Content-Type: ' . ($extension === 'docx'
        ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        : ($extension === 'doc' ? 'application/msword' : 'application/pdf')));
    header('Content-Disposition: attachment; filename="cognitive-screening-report-' . $id . '.' . $extension . '"');
    header('Content-Length: ' . filesize($path));
    readfile($path);
} catch (Throwable $e) {
    http_response_code(500);
    echo $e->getMessage();
}
