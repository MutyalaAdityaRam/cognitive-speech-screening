import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class ApiService {
  // ignore: constant_identifier_names
  static const String BASE_URL = 'http://10.78.191.50/speech_project/api';
  static const String baseUrl = BASE_URL;
  static const Duration timeoutDuration = Duration(minutes: 3);

  static http.Client _createClient() {
    return http.Client();
  }

  static Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final client = _createClient();
    try {
      final response = await client
          .post(
            Uri.parse('$baseUrl/login.php'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'email': email, 'password': password}),
          )
          .timeout(timeoutDuration);
      if (response.statusCode == 200 || response.statusCode == 201) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        return {
          'error':
              'Login failed: HTTP ${response.statusCode} - ${response.body}'
        };
      }
    } catch (e) {
      return {'error': 'Login connection error: $e'};
    } finally {
      client.close();
    }
  }

  static Future<Map<String, dynamic>> register({
    required String name,
    required String email,
    required String password,
    int? age,
  }) async {
    final client = _createClient();
    try {
      final response = await client
          .post(
            Uri.parse('$baseUrl/register.php'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'name': name,
              'email': email,
              'password': password,
              'age': age,
            }),
          )
          .timeout(timeoutDuration);
      if (response.statusCode == 200 || response.statusCode == 201) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        return {
          'error':
              'Register failed: HTTP ${response.statusCode} - ${response.body}'
        };
      }
    } catch (e) {
      return {'error': 'Register connection error: $e'};
    } finally {
      client.close();
    }
  }

  static Future<Map<String, dynamic>> predict({
    required int userId,
    String? userName,
    required File audioFile,
  }) async {
    final client = _createClient();
    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/predict.php'),
      );
      request.fields['user_id'] = userId.toString();
      if ((userName ?? '').trim().isNotEmpty) {
        request.fields['user_name'] = userName!.trim();
      }
      request.files.add(await http.MultipartFile.fromPath(
        'audio',
        audioFile.path,
      ));
      final streamedResponse = await request.send().timeout(timeoutDuration);
      final responseBody = await streamedResponse.stream.bytesToString();
      if (streamedResponse.statusCode == 200 ||
          streamedResponse.statusCode == 201) {
        return jsonDecode(responseBody) as Map<String, dynamic>;
      } else {
        return {
          'error':
              'Prediction failed: HTTP ${streamedResponse.statusCode} - $responseBody'
        };
      }
    } catch (e) {
      return {'error': 'Prediction connection error: $e'};
    } finally {
      client.close();
    }
  }

  static Future<Map<String, dynamic>> chat({
    required int userId,
    required String question,
    String? userName,
    Map<String, dynamic>? context,
  }) async {
    final client = _createClient();
    try {
      final mergedContext = <String, dynamic>{
        if (context != null) ...context,
        if ((userName ?? '').trim().isNotEmpty) 'user_name': userName!.trim(),
      };
      final response = await client
          .post(
            Uri.parse('$baseUrl/chat.php'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'user_id': userId,
              'question': question,
              'context': mergedContext,
            }),
          )
          .timeout(timeoutDuration);
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        return {
          'error': 'Chat failed: HTTP ${response.statusCode} - ${response.body}'
        };
      }
    } catch (e) {
      return {'error': 'Chat connection error: $e'};
    } finally {
      client.close();
    }
  }

  static Future<File> downloadReport({
    required int reportId,
    required String format,
    required Directory directory,
  }) async {
    final client = _createClient();
    try {
      final response = await client
          .get(Uri.parse(
              '$baseUrl/download-report.php?id=$reportId&format=$format'))
          .timeout(timeoutDuration);
      if (response.statusCode != 200) {
        throw Exception(
            'Download failed: HTTP ${response.statusCode} - ${response.body}');
      }
      final path =
          '${directory.path}${Platform.pathSeparator}cognitive-screening-report-$reportId.$format';
      final file = File(path);
      await file.writeAsBytes(response.bodyBytes);
      return file;
    } finally {
      client.close();
    }
  }

  static Future<List<dynamic>> getHistory({
    required int userId,
  }) async {
    final client = _createClient();
    try {
      final response = await client
          .post(
            Uri.parse('$baseUrl/history.php'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'user_id': userId}),
          )
          .timeout(timeoutDuration);
      if (response.statusCode == 200) {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        return body['reports'] as List<dynamic>;
      } else {
        return [];
      }
    } catch (e) {
      return [];
    } finally {
      client.close();
    }
  }
}
