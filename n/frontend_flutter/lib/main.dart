import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'services/api_service.dart';

void main() => runApp(const ScreeningApp());

class ScreeningApp extends StatelessWidget {
  const ScreeningApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Cognitive Speech Screening',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF167A7F)),
        useMaterial3: true,
        cardTheme: const CardThemeData(
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(8)),
          ),
        ),
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF4DB6AC),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
        cardTheme: const CardThemeData(
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(8)),
          ),
        ),
      ),
      themeMode: ThemeMode.system,
      home: const AuthGate(),
    );
  }
}

class AppState {
  static int userId = 1;
  static String userName = 'Patient';
  static const _userIdKey = 'user_id';
  static const _userNameKey = 'user_name';

  static Future<bool> loadSession() async {
    final prefs = await SharedPreferences.getInstance();
    final storedUserId = prefs.getInt(_userIdKey);
    final storedUserName = prefs.getString(_userNameKey);
    if (storedUserId == null || storedUserId <= 0) {
      return false;
    }
    userId = storedUserId;
    userName = (storedUserName == null || storedUserName.trim().isEmpty)
        ? 'Patient'
        : storedUserName.trim();
    return true;
  }

  static Future<void> saveSession({
    required int id,
    required String name,
  }) async {
    final cleanName = name.trim().isEmpty ? 'Patient' : name.trim();
    userId = id;
    userName = cleanName;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_userIdKey, id);
    await prefs.setString(_userNameKey, cleanName);
  }

  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_userIdKey);
    await prefs.remove(_userNameKey);
    userId = 1;
    userName = 'Patient';
  }
}

class AuthGate extends StatefulWidget {
  const AuthGate({super.key});

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  late Future<bool> _session;

  @override
  void initState() {
    super.initState();
    _session = AppState.loadSession();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<bool>(
      future: _session,
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const Scaffold(
              body: Center(child: CircularProgressIndicator()));
        }
        return snapshot.data! ? const HomeScreen() : const LoginScreen();
      },
    );
  }
}

class ProjectLogo extends StatelessWidget {
  const ProjectLogo({super.key, this.size = 72});

  final double size;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: colorScheme.primaryContainer,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          Icon(
            Icons.psychology_alt_outlined,
            size: size * .52,
            color: colorScheme.primary,
          ),
          Positioned(
            bottom: size * .18,
            right: size * .18,
            child: Icon(
              Icons.graphic_eq,
              size: size * .28,
              color: colorScheme.secondary,
            ),
          ),
        ],
      ),
    );
  }
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final email = TextEditingController(text: 'patient@example.com');
  final password = TextEditingController();
  bool isLogging = false;
  String? error;

  Future<void> login() async {
    if (email.text.trim().isEmpty || password.text.isEmpty) {
      setState(() => error = 'Email and password are required.');
      return;
    }

    setState(() {
      isLogging = true;
      error = null;
    });

    try {
      final body = await ApiService.login(
        email: email.text.trim(),
        password: password.text,
      );

      if (body['error'] != null) {
        throw Exception(body['error'] ?? 'Login failed');
      }

      await AppState.saveSession(
        id: (body['user_id'] as num).toInt(),
        name: (body['name'] ?? email.text.split('@').first).toString(),
      );

      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => const HomeScreen()),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          isLogging = false;
          error = e.toString().replaceFirst('Exception: ', '');
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 460),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    'Cognitive Speech Screening',
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const SizedBox(height: 18),
                  const Center(child: ProjectLogo()),
                  const SizedBox(height: 24),
                  TextField(
                    controller: email,
                    enabled: !isLogging,
                    decoration: const InputDecoration(
                      labelText: 'Email',
                      prefixIcon: Icon(Icons.mail_outline),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: password,
                    enabled: !isLogging,
                    obscureText: true,
                    decoration: const InputDecoration(
                      labelText: 'Password',
                      prefixIcon: Icon(Icons.lock_outline),
                    ),
                  ),
                  if (error != null) ...[
                    const SizedBox(height: 12),
                    Text(
                      error!,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                        fontSize: 13,
                      ),
                    ),
                  ],
                  const SizedBox(height: 20),
                  FilledButton.icon(
                    onPressed: isLogging ? null : login,
                    icon: isLogging
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              valueColor: AlwaysStoppedAnimation<Color>(
                                Colors.white,
                              ),
                            ),
                          )
                        : const Icon(Icons.login),
                    label: Text(isLogging ? 'Logging in...' : 'Login'),
                  ),
                  TextButton(
                    onPressed: isLogging
                        ? null
                        : () => Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => const ProfileScreen(),
                              ),
                            ),
                    child: const Text('Create account'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    email.dispose();
    password.dispose();
    super.dispose();
  }
}

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final name = TextEditingController();
  final email = TextEditingController(text: 'patient@example.com');
  final password = TextEditingController();
  final age = TextEditingController();
  bool saving = false;
  String? error;

  Future<void> saveProfile() async {
    if (name.text.trim().isEmpty ||
        email.text.trim().isEmpty ||
        password.text.isEmpty) {
      setState(() => error = 'Full name, email, and password are required.');
      return;
    }

    if (password.text.length < 6) {
      setState(() => error = 'Password must be at least 6 characters.');
      return;
    }

    setState(() {
      saving = true;
      error = null;
    });
    try {
      final body = await ApiService.register(
        name: name.text.trim(),
        email: email.text.trim(),
        password: password.text,
        age: int.tryParse(age.text.trim()),
      );

      if (body['error'] != null) {
        throw Exception(body['error'] ?? 'Account creation failed');
      }

      await AppState.saveSession(
        id: (body['user_id'] as num).toInt(),
        name: (body['name'] ?? name.text.trim()).toString(),
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Account created successfully.'),
            duration: Duration(seconds: 2),
          ),
        );
        Navigator.pushAndRemoveUntil(
          context,
          MaterialPageRoute(builder: (_) => const HomeScreen()),
          (_) => false,
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          saving = false;
          error = e.toString().replaceFirst('Exception: ', '');
        });
      }
    }
  }

  @override
  void dispose() {
    name.dispose();
    email.dispose();
    password.dispose();
    age.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create Account')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          TextField(
            controller: name,
            enabled: !saving,
            decoration: const InputDecoration(labelText: 'Full name'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: email,
            enabled: !saving,
            keyboardType: TextInputType.emailAddress,
            decoration: const InputDecoration(labelText: 'Email'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: password,
            enabled: !saving,
            obscureText: true,
            decoration: const InputDecoration(
              labelText: 'Password',
              helperText: 'Minimum 6 characters',
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: age,
            enabled: !saving,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Age (optional)'),
          ),
          if (error != null) ...[
            const SizedBox(height: 12),
            Text(
              error!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ],
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: saving ? null : saveProfile,
        icon: saving
            ? const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : const Icon(Icons.check),
        label: Text(saving ? 'Creating' : 'Create Account'),
      ),
    );
  }
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key, this.initialContext, this.initialMessages});

  final Map<String, dynamic>? initialContext;
  final List<Map<String, dynamic>>? initialMessages;

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final List<Map<String, dynamic>> messages = [];
  final TextEditingController _controller = TextEditingController();
  final Map<String, dynamic> chatContext = {};
  bool isLoading = false;
  bool isLoadingReports = false;
  Map<String, dynamic>? selectedReport;

  @override
  void initState() {
    super.initState();
    if (widget.initialContext != null) {
      chatContext.addAll(widget.initialContext!);
    }
    if (widget.initialMessages != null) {
      messages.addAll(widget.initialMessages!);
    } else {
      messages.add({
        'sender': 'system',
        'text':
            'Hi ${AppState.userName}, how can I help you understand your screening report today?'
      });
    }
  }

  Future<void> attachGeneratedReport() async {
    if (isLoadingReports) return;
    setState(() => isLoadingReports = true);
    try {
      final reports = await ApiService.getHistory(userId: AppState.userId);
      if (!mounted) return;
      setState(() => isLoadingReports = false);
      if (reports.isEmpty) {
        setState(() {
          messages.add({
            'sender': 'system',
            'text':
                'No generated reports are available yet. Please complete a speech screening first, then I can help explain the generated report.'
          });
        });
        return;
      }

      final picked = await showModalBottomSheet<Map<String, dynamic>>(
        context: context,
        showDragHandle: true,
        builder: (context) {
          return SafeArea(
            child: ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
              itemCount: reports.length,
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final report = Map<String, dynamic>.from(
                    reports[index] as Map<dynamic, dynamic>);
                final title =
                    (report['prediction'] ?? 'Generated report').toString();
                final createdAt = (report['created_at'] ?? '').toString();
                final confidence = (report['confidence'] ?? '').toString();
                return ListTile(
                  leading: const Icon(Icons.description_outlined),
                  title: Text(title),
                  subtitle: Text(
                    [
                      if (confidence.isNotEmpty) 'Confidence: $confidence',
                      if (createdAt.isNotEmpty) createdAt,
                    ].join('  '),
                  ),
                  onTap: () => Navigator.pop(context, report),
                );
              },
            ),
          );
        },
      );

      if (picked == null || !mounted) return;
      final reportText =
          (picked['report_text'] ?? picked['clinician_report'] ?? '')
              .toString()
              .trim();
      if (reportText.isEmpty) {
        setState(() {
          messages.add({
            'sender': 'system',
            'text':
                'This generated report does not include report text that I can explain.'
          });
        });
        return;
      }

      setState(() {
        selectedReport = picked;
        chatContext['uploaded_report_text'] = reportText;
        chatContext['report_text'] = reportText;
        chatContext['latest_screening_result'] = {
          'prediction': picked['prediction'],
          'confidence': picked['confidence'],
          'final_probability': picked['final_probability'],
          'transcript': picked['transcript'],
        };
        messages.add({
          'sender': 'system',
          'text':
              'I added your generated screening report. You can ask me to explain the risk summary, confidence, observations, or recommendation.'
        });
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        isLoadingReports = false;
        messages.add({
          'sender': 'system',
          'text':
              'I could not load your generated reports right now. Please try again.'
        });
      });
    }
  }

  Future<void> sendMessage() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    setState(() {
      messages.add({'sender': 'user', 'text': text});
      isLoading = true;
    });
    _controller.clear();

    try {
      final body = await ApiService.chat(
        userId: AppState.userId,
        question: text,
        userName: AppState.userName,
        context: chatContext,
      );

      if (body['error'] != null) {
        throw Exception(body['error'] ?? 'Failed to get response');
      }

      setState(() {
        messages.add({'sender': 'system', 'text': body['answer']});
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        messages.add({
          'sender': 'system',
          'text': 'Error: ${e.toString().replaceFirst('Exception: ', '')}'
        });
        isLoading = false;
      });
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Cognitive Support Chat'),
        elevation: 1,
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: messages.length + (isLoading ? 1 : 0),
              itemBuilder: (context, index) {
                if (isLoading && index == messages.length) {
                  return const Align(
                    alignment: Alignment.centerLeft,
                    child: Card(
                      child: Padding(
                        padding:
                            EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                            SizedBox(width: 12),
                            Text('Typing...'),
                          ],
                        ),
                      ),
                    ),
                  );
                }
                final message = messages[index];
                final isUser = message['sender'] == 'user';
                return Align(
                  alignment:
                      isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Card(
                    color: isUser
                        ? Theme.of(context).colorScheme.primaryContainer
                        : Theme.of(context).colorScheme.surface,
                    child: Padding(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 8),
                      child: Text(message['text']),
                    ),
                  ),
                );
              },
            ),
          ),
          if (selectedReport != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 0, 12, 8),
              child: InputChip(
                avatar: const Icon(Icons.description_outlined),
                label: Text(
                  'Generated report added: ${selectedReport!['prediction'] ?? 'Report'}',
                ),
                onDeleted: () {
                  setState(() {
                    selectedReport = null;
                    chatContext.remove('uploaded_report_text');
                    chatContext.remove('report_text');
                    chatContext.remove('latest_screening_result');
                  });
                },
              ),
            ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  IconButton.outlined(
                    tooltip: 'Add generated report',
                    onPressed: isLoading || isLoadingReports
                        ? null
                        : attachGeneratedReport,
                    icon: isLoadingReports
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.post_add_outlined),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      decoration: const InputDecoration(
                        hintText: 'Ask about cognitive screening...',
                        border: OutlineInputBorder(),
                      ),
                      onSubmitted: (_) => sendMessage(),
                      enabled: !isLoading,
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    onPressed: isLoading ? null : sendMessage,
                    icon: const Icon(Icons.send),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class ReadingPassage {
  const ReadingPassage({
    required this.id,
    required this.type,
    required this.difficulty,
    required this.text,
  });

  final String id;
  final String type;
  final String difficulty;
  final String text;

  List<String> get sentences {
    final matches = RegExp(r'[^.!?]+[.!?]').allMatches(text);
    final parsed = matches.map((match) => match.group(0)!.trim()).toList();
    return parsed.isEmpty ? [text] : parsed;
  }

  factory ReadingPassage.fromJson(Map<String, dynamic> json) {
    return ReadingPassage(
      id: (json['id'] ?? '').toString(),
      type: (json['type'] ?? 'Reading passage').toString(),
      difficulty: (json['difficulty'] ?? 'standard').toString(),
      text: (json['text'] ?? '').toString(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<ReadingPassage> passages = const [];
  int index = 0;
  bool loading = false;
  bool recording = false;
  bool preparing = false;
  int countdown = 0;
  int elapsedSeconds = 0;
  double textScale = 1.0;
  Map<String, dynamic>? report;
  final recorder = AudioRecorder();
  Timer? recordingTimer;
  Timer? countdownTimer;

  ReadingPassage? get currentPassage =>
      passages.isEmpty ? null : passages[index % passages.length];

  @override
  void initState() {
    super.initState();
    loadPassages();
  }

  Future<void> loadPassages() async {
    final raw = await rootBundle.loadString('assets/reading_passages.json');
    final decoded = jsonDecode(raw) as List<dynamic>;
    final loaded = decoded
        .map((item) => ReadingPassage.fromJson(item as Map<String, dynamic>))
        .where((passage) => passage.text.trim().isNotEmpty)
        .toList();
    if (!mounted) return;
    setState(() {
      passages = loaded;
      index = loaded.isEmpty ? 0 : Random().nextInt(loaded.length);
    });
  }

  Future<void> uploadAudio() async {
    final picked = await FilePicker.platform.pickFiles(type: FileType.audio);
    if (picked?.files.single.path == null) return;
    await submitAudioFile(picked!.files.single.path!);
  }

  Future<void> submitAudioFile(String path) async {
    setState(() => loading = true);
    try {
      final body = await ApiService.predict(
        userId: AppState.userId,
        userName: AppState.userName,
        audioFile: File(path),
      );

      if (body['error'] != null) {
        throw Exception(body['error'] ?? 'Upload failed');
      }

      setState(() {
        loading = false;
        report = body;
        if (body['status'] == 'needs_restart') {
          index = passages.isEmpty ? 0 : (index + 1) % passages.length;
          body['message'] =
              'No clear speech detected. Please read the paragraph again in a quiet environment.';
        }
      });
    } catch (e) {
      setState(() {
        loading = false;
        report = {'error': 'Upload failed: $e'};
      });
    }
  }

  Future<void> toggleRecording() async {
    if (recording) {
      final path = await recorder.stop();
      if (!mounted) return;
      recordingTimer?.cancel();
      setState(() => recording = false);
      if (path == null || !File(path).existsSync()) {
        setState(() {
          report = {'error': 'Recording failed. Please try again.'};
        });
        return;
      }
      await submitAudioFile(path);
      return;
    }

    final allowed = await recorder.hasPermission();
    if (!allowed) {
      setState(() {
        report = {
          'error': 'Microphone permission is required to record voice.',
        };
      });
      return;
    }

    final directory = await getTemporaryDirectory();
    final path =
        '${directory.path}${Platform.pathSeparator}speech_${DateTime.now().millisecondsSinceEpoch}.wav';
    try {
      await recorder.start(
        const RecordConfig(
          encoder: AudioEncoder.wav,
          sampleRate: 16000,
          numChannels: 1,
        ),
        path: path,
      );
      if (mounted) {
        setState(() {
          recording = true;
          elapsedSeconds = 0;
        });
        recordingTimer?.cancel();
        recordingTimer = Timer.periodic(const Duration(seconds: 1), (_) {
          if (mounted) setState(() => elapsedSeconds++);
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          report = {'error': 'Recording failed: $e'};
        });
      }
    }
  }

  Future<void> startReadingFlow() async {
    if (recording || preparing || loading) return;
    final allowed = await recorder.hasPermission();
    if (!allowed) {
      setState(() {
        report = {
          'error': 'Microphone permission is required to record voice.',
        };
      });
      return;
    }
    setState(() {
      preparing = true;
      countdown = 3;
      report = null;
    });
    countdownTimer?.cancel();
    countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) async {
      if (!mounted) return;
      if (countdown <= 1) {
        timer.cancel();
        setState(() {
          preparing = false;
          countdown = 0;
        });
        await toggleRecording();
      } else {
        setState(() => countdown--);
      }
    });
  }

  @override
  void dispose() {
    recordingTimer?.cancel();
    countdownTimer?.cancel();
    recorder.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Speech Screening'),
        actions: [
          IconButton(
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const ChatScreen()),
            ),
            icon: const Icon(Icons.chat_outlined),
          ),
          IconButton(
            tooltip: 'Profile',
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const UserProfileScreen()),
            ),
            icon: const Icon(Icons.account_circle_outlined),
          ),
          IconButton(
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const HistoryScreen()),
            ),
            icon: const Icon(Icons.history),
          ),
        ],
      ),
      body: AnimatedSwitcher(
        duration: const Duration(milliseconds: 300),
        child: loading ? const LoadingPanel() : buildContent(context),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: loading ? null : uploadAudio,
        icon: const Icon(Icons.upload_file),
        label: const Text('Upload audio'),
      ),
    );
  }

  Widget buildContent(BuildContext context) {
    final passage = currentPassage;
    final progress = recording ? (elapsedSeconds / 90).clamp(0.0, 1.0) : 0.0;
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text(
          'Welcome back, ${AppState.userName}',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 4),
        Text(
          'You can record a speech sample, upload audio, or review generated reports.',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 20),
        if (passage == null)
          const Card(
            child: Padding(
              padding: EdgeInsets.all(18),
              child: Center(child: CircularProgressIndicator()),
            ),
          )
        else
          ReadingAssessmentCard(
            passage: passage,
            textScale: textScale,
            recording: recording,
            preparing: preparing,
            countdown: countdown,
            elapsedSeconds: elapsedSeconds,
            progress: progress,
            onTextScaleChanged: (value) => setState(() => textScale = value),
            onNextPassage: () => setState(
              () =>
                  index = passages.isEmpty ? 0 : (index + 1) % passages.length,
            ),
            onStart: startReadingFlow,
            onStop: toggleRecording,
          ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: loading ? null : uploadAudio,
          icon: const Icon(Icons.upload_file),
          label: const Text('Upload existing audio'),
        ),
        const SizedBox(height: 24),
        if (report != null) ReportPanel(report: report!),
      ],
    );
  }
}

class ReadingAssessmentCard extends StatelessWidget {
  const ReadingAssessmentCard({
    super.key,
    required this.passage,
    required this.textScale,
    required this.recording,
    required this.preparing,
    required this.countdown,
    required this.elapsedSeconds,
    required this.progress,
    required this.onTextScaleChanged,
    required this.onNextPassage,
    required this.onStart,
    required this.onStop,
  });

  final ReadingPassage passage;
  final double textScale;
  final bool recording;
  final bool preparing;
  final int countdown;
  final int elapsedSeconds;
  final double progress;
  final ValueChanged<double> onTextScaleChanged;
  final VoidCallback onNextPassage;
  final VoidCallback onStart;
  final VoidCallback onStop;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final sentences = passage.sentences;
    final highlightedIndex = recording && sentences.isNotEmpty
        ? min(sentences.length - 1, elapsedSeconds ~/ 18)
        : 0;
    return Card(
      color: colorScheme.surfaceContainerHighest.withValues(alpha: .45),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Icon(Icons.record_voice_over_outlined,
                    color: colorScheme.primary),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Guided Reading Assessment',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      Text(
                        '${passage.type} · ${passage.difficulty}',
                        style: Theme.of(context).textTheme.labelMedium,
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              'Read the passage aloud at a natural pace. Use a quiet environment and continue until the final sentence is complete.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 6),
            Text(
              'Use New Passage to rotate passages, or Start Reading again if you need to repeat the instructions.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: colorScheme.onSurfaceVariant,
                  ),
            ),
            const SizedBox(height: 14),
            LinearProgressIndicator(
              value: recording ? progress : null,
              minHeight: 6,
              borderRadius: BorderRadius.circular(6),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Text('Time: ${_formatSeconds(elapsedSeconds)}'),
                const Spacer(),
                Text('${sentences.length} sentences'),
              ],
            ),
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: colorScheme.outlineVariant),
              ),
              child: RichText(
                textAlign: TextAlign.center,
                text: TextSpan(
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        fontSize: 21 * textScale,
                        height: 1.55,
                        color: colorScheme.onSurface,
                        fontWeight: FontWeight.w500,
                      ),
                  children: [
                    for (var i = 0; i < sentences.length; i++)
                      TextSpan(
                        text: '${sentences[i]} ',
                        style: i == highlightedIndex
                            ? TextStyle(
                                backgroundColor: colorScheme.primaryContainer,
                                color: colorScheme.onPrimaryContainer,
                              )
                            : null,
                      ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                const Icon(Icons.format_size, size: 20),
                Expanded(
                  child: Slider(
                    value: textScale,
                    min: .9,
                    max: 1.35,
                    divisions: 3,
                    label: '${(textScale * 100).round()}%',
                    onChanged: onTextScaleChanged,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (preparing)
              Center(
                child: Text(
                  'Starting in $countdown',
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
              )
            else if (recording)
              Column(
                children: [
                  const MicWaveform(),
                  const SizedBox(height: 10),
                  FilledButton.icon(
                    onPressed: onStop,
                    icon: const Icon(Icons.stop),
                    label: const Text('Stop and Analyze'),
                  ),
                ],
              )
            else
              Wrap(
                spacing: 10,
                runSpacing: 10,
                alignment: WrapAlignment.center,
                children: [
                  FilledButton.icon(
                    onPressed: onStart,
                    icon: const Icon(Icons.mic),
                    label: const Text('Start Reading'),
                  ),
                  OutlinedButton.icon(
                    onPressed: onNextPassage,
                    icon: const Icon(Icons.shuffle),
                    label: const Text('New Passage'),
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }

  String _formatSeconds(int seconds) {
    final minutes = seconds ~/ 60;
    final remaining = seconds % 60;
    return '$minutes:${remaining.toString().padLeft(2, '0')}';
  }
}

class MicWaveform extends StatefulWidget {
  const MicWaveform({super.key});

  @override
  State<MicWaveform> createState() => _MicWaveformState();
}

class _MicWaveformState extends State<MicWaveform>
    with SingleTickerProviderStateMixin {
  late final AnimationController controller;

  @override
  void initState() {
    super.initState();
    controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final color = Theme.of(context).colorScheme.primary;
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        return Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: List.generate(7, (i) {
            final phase = (controller.value + i * .12) % 1;
            final height = 16 + (sin(phase * pi) * 28);
            return Container(
              width: 7,
              height: height,
              margin: const EdgeInsets.symmetric(horizontal: 3),
              decoration: BoxDecoration(
                color: color.withValues(alpha: .35 + phase * .55),
                borderRadius: BorderRadius.circular(8),
              ),
            );
          }),
        );
      },
    );
  }
}

class UserProfileScreen extends StatelessWidget {
  const UserProfileScreen({super.key});

  Future<void> _logout(BuildContext context) async {
    await AppState.logout();
    if (!context.mounted) return;
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (_) => const LoginScreen()),
      (_) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Center(child: ProjectLogo(size: 88)),
          const SizedBox(height: 20),
          Text(
            AppState.userName,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 4),
          Text(
            'Signed in to Cognitive Speech Screening',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 24),
          ListTile(
            leading: const Icon(Icons.badge_outlined),
            title: const Text('User ID'),
            subtitle: Text(AppState.userId.toString()),
          ),
          const ListTile(
            leading: Icon(Icons.privacy_tip_outlined),
            title: Text('Session'),
            subtitle: Text(
              'This device will remember your login until you logout.',
            ),
          ),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: () => _logout(context),
            icon: const Icon(Icons.logout),
            label: const Text('Logout'),
          ),
        ],
      ),
    );
  }
}

class LoadingPanel extends StatelessWidget {
  const LoadingPanel({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: List.generate(
        5,
        (i) => Container(
          margin: const EdgeInsets.only(bottom: 14),
          height: i == 0 ? 84 : 46,
          decoration: BoxDecoration(
            color: Colors.teal.withValues(alpha: .08),
            borderRadius: BorderRadius.circular(8),
          ),
        ),
      ),
    );
  }
}

class ReportPanel extends StatefulWidget {
  const ReportPanel({super.key, required this.report});
  final Map<String, dynamic> report;

  @override
  State<ReportPanel> createState() => _ReportPanelState();
}

class _ReportPanelState extends State<ReportPanel> {
  String? downloadMessage;
  bool downloading = false;
  String selectedFormat = 'pdf';

  Future<void> download(String format) async {
    final id = (widget.report['report_id'] as num?)?.toInt();
    if (id == null) {
      setState(() => downloadMessage = 'Report id is unavailable.');
      return;
    }
    setState(() {
      downloading = true;
      downloadMessage = null;
    });
    try {
      final directory = await getApplicationDocumentsDirectory();
      final file = await ApiService.downloadReport(
        reportId: id,
        format: format,
        directory: directory,
      );
      if (mounted) {
        setState(() {
          downloading = false;
          downloadMessage = 'Saved to ${file.path}';
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          downloading = false;
          downloadMessage = e.toString().replaceFirst('Exception: ', '');
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final report = widget.report;
    if ((report['error'] ?? '').toString().isNotEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text('Error: ${report['error']}'),
        ),
      );
    }
    if (report['status'] == 'needs_restart') {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text(
            report['message'] ?? 'No voice detected. Please restart reading.',
          ),
        ),
      );
    }
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${AppState.userName}, I have completed your cognitive speech screening analysis.',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text('Risk Level: ${report['prediction'] ?? report['risk_level']}'),
            const SizedBox(height: 8),
            Text(
              'Confidence: ${(report['confidence'] ?? 0).toString()}',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 8),
            if ((report['transcript'] ?? '').toString().isNotEmpty) ...[
              Text('Transcript', style: Theme.of(context).textTheme.labelLarge),
              Text(report['transcript']),
              const SizedBox(height: 8),
            ],
            Text(report['final_report'] ?? report['report_text'] ?? ''),
            const SizedBox(height: 14),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(
                      value: 'pdf',
                      icon: Icon(Icons.picture_as_pdf_outlined),
                      label: Text('PDF'),
                    ),
                    ButtonSegment(
                      value: 'doc',
                      icon: Icon(Icons.description_outlined),
                      label: Text('Word'),
                    ),
                  ],
                  selected: {selectedFormat},
                  onSelectionChanged: downloading
                      ? null
                      : (value) => setState(() => selectedFormat = value.first),
                ),
                FilledButton.icon(
                  onPressed:
                      downloading ? null : () => download(selectedFormat),
                  icon: downloading
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.download_outlined),
                  label: const Text('Download Selected'),
                ),
                OutlinedButton.icon(
                  onPressed: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => PdfPreviewScreen(report: report),
                    ),
                  ),
                  icon: const Icon(Icons.preview_outlined),
                  label: const Text('Preview'),
                ),
              ],
            ),
            if (downloadMessage != null) ...[
              const SizedBox(height: 8),
              Text(
                downloadMessage!,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class PdfPreviewScreen extends StatelessWidget {
  const PdfPreviewScreen({super.key, required this.report});
  final Map<String, dynamic> report;

  @override
  Widget build(BuildContext context) {
    final text = report['final_report'] ?? report['report_text'] ?? '';
    return Scaffold(
      appBar: AppBar(title: const Text('PDF Preview')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(
            'Cognitive Screening Report',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 12),
          Text(
              'Risk Level: ${report['prediction'] ?? report['risk_level'] ?? 'Unknown'}'),
          Text('Confidence: ${(report['confidence'] ?? '').toString()}'),
          const SizedBox(height: 16),
          Text(text),
        ],
      ),
    );
  }
}

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  late Future<List<dynamic>> reports;
  Timer? timer;

  @override
  void initState() {
    super.initState();
    reports = fetchReports();
    timer = Timer.periodic(const Duration(seconds: 3), (_) {
      if (mounted) setState(() => reports = fetchReports());
    });
  }

  @override
  void dispose() {
    timer?.cancel();
    super.dispose();
  }

  Future<List<dynamic>> fetchReports() async {
    return await ApiService.getHistory(userId: AppState.userId);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Report History')),
      body: FutureBuilder<List<dynamic>>(
        future: reports,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          }
          if (!snapshot.hasData) return const LoadingPanel();
          return ListView(
            children: snapshot.data!
                .map(
                  (item) => ListTile(
                    leading: const Icon(Icons.description_outlined),
                    title: Text(item['prediction'] ?? 'Report'),
                    subtitle: Text(
                      'Confidence: ${(item['confidence'] ?? '').toString()}  ${item['created_at'] ?? ''}',
                    ),
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => ReportDetailScreen(id: item['id']),
                      ),
                    ),
                  ),
                )
                .toList(),
          );
        },
      ),
    );
  }
}

class ReportDetailScreen extends StatelessWidget {
  const ReportDetailScreen({super.key, required this.id});
  final dynamic id;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Report Details')),
      body: FutureBuilder<List<dynamic>>(
        future: ApiService.getHistory(userId: AppState.userId),
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          }
          if (!snapshot.hasData) return const LoadingPanel();
          final report =
              snapshot.data!.firstWhere((r) => r['id'] == id, orElse: () => {});
          return ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Text(
                report['prediction'] ?? report['final_risk_level'] ?? 'Report',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 12),
              Text(report['report_text'] ?? report['clinician_report'] ?? ''),
              const SizedBox(height: 16),
              ReportDownloadControls(reportId: (id as num).toInt()),
            ],
          );
        },
      ),
    );
  }
}

class ReportDownloadControls extends StatefulWidget {
  const ReportDownloadControls({super.key, required this.reportId});

  final int reportId;

  @override
  State<ReportDownloadControls> createState() => _ReportDownloadControlsState();
}

class _ReportDownloadControlsState extends State<ReportDownloadControls> {
  String selectedFormat = 'pdf';
  bool downloading = false;
  String? message;

  Future<void> download() async {
    setState(() {
      downloading = true;
      message = null;
    });
    try {
      final directory = await getApplicationDocumentsDirectory();
      final file = await ApiService.downloadReport(
        reportId: widget.reportId,
        format: selectedFormat,
        directory: directory,
      );
      if (!mounted) return;
      setState(() {
        downloading = false;
        message = 'Saved to ${file.path}';
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        downloading = false;
        message = e.toString().replaceFirst('Exception: ', '');
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(
                  value: 'pdf',
                  icon: Icon(Icons.picture_as_pdf_outlined),
                  label: Text('PDF'),
                ),
                ButtonSegment(
                  value: 'doc',
                  icon: Icon(Icons.description_outlined),
                  label: Text('Word'),
                ),
              ],
              selected: {selectedFormat},
              onSelectionChanged: downloading
                  ? null
                  : (value) => setState(() => selectedFormat = value.first),
            ),
            FilledButton.icon(
              onPressed: downloading ? null : download,
              icon: downloading
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.download_outlined),
              label: const Text('Download Selected'),
            ),
          ],
        ),
        if (message != null) ...[
          const SizedBox(height: 8),
          Text(message!, style: Theme.of(context).textTheme.bodySmall),
        ],
      ],
    );
  }
}
