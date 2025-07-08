import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:googleapis/gmail/v1.dart' as gmail;
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dashboard_screen.dart';

class GmailSignInView extends StatefulWidget {
  @override
  _GmailSignInViewState createState() => _GmailSignInViewState();
}

class _GmailSignInViewState extends State<GmailSignInView> {
  GoogleSignInAccount? _user;
  gmail.GmailApi? _gmailApi;

  final _scopes = [
    gmail.GmailApi.gmailReadonlyScope,
  ];

  Future<void> _signIn() async {
    try {
      final googleSignIn = GoogleSignIn.standard(scopes: _scopes);
      final account = await googleSignIn.signIn();
      if (account == null) return;

      final auth = await account.authentication;
      final client = GoogleHttpClient({
        'Authorization': 'Bearer ${auth.accessToken}',
        'X-Goog-AuthUser': '0',
      });

      final gmailApi = gmail.GmailApi(client);
      setState(() {
        _user = account;
        _gmailApi = gmailApi;
      });

      final reminders = await _loadCreditCardReminders();

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => DashboardScreen(reminders: reminders),
        ),
      );
    } catch (e) {
      print('Sign in error: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Failed to sign in. Try again.")),
      );
    }
  }

  Future<List<Map<String, String>>> _loadCreditCardReminders() async {
    try {
      final messagesResponse = await _gmailApi!.users.messages.list(
        'me',
        maxResults: 30,
        labelIds: ['INBOX'],
        q: 'subject:(bill OR statement OR due OR payment OR invoice)',
      );

      if (messagesResponse.messages == null || messagesResponse.messages!.isEmpty) {
        print('No messages found.');
        return [];
      }

      List<Map<String, String>> reminders = [];

      for (var message in messagesResponse.messages!) {
        final fullMessage = await _gmailApi!.users.messages.get('me', message.id!);

        final fromHeader = fullMessage.payload?.headers?.firstWhere(
          (header) => header.name == 'From',
          orElse: () => gmail.MessagePartHeader(name: 'From', value: ''),
        );

        final subjectHeader = fullMessage.payload?.headers?.firstWhere(
          (header) => header.name == 'Subject',
          orElse: () => gmail.MessagePartHeader(name: 'Subject', value: '(No Subject)'),
        );

        final snippet = fullMessage.snippet ?? '';
        final from = fromHeader?.value ?? '';

        final amountRegex = RegExp(r'(AED|USD|INR|SAR|EUR)?\s?(\d{1,3}(,\d{3})*|\d+)(\.\d{2})?');
        final dateRegex = RegExp(r'\b(\d{1,2}\s?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s?\d{4})\b', caseSensitive: false);

        final amountMatch = amountRegex.firstMatch(snippet);
        final dateMatch = dateRegex.firstMatch(snippet);

        final status = snippet.toLowerCase().contains("paid") ? "Paid" : "Pending";

        reminders.add({
          'card': from.split('<').first.trim(),
          'due': dateMatch?.group(0) ?? 'Date not found',
          'amount': amountMatch?.group(0) ?? 'Amount not found',
          'status': status,
        });
      }

      return reminders;
    } catch (e) {
      print('Failed to load inbox: $e');
      return [];
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Credit Email Insights'),
        actions: [
          if (_user != null)
            IconButton(
              icon: Icon(Icons.logout),
              onPressed: () async {
                await GoogleSignIn().signOut();
                setState(() {
                  _user = null;
                  _gmailApi = null;
                });
              },
            )
        ],
      ),
      body: Center(
        child: ElevatedButton.icon(
          icon: Icon(Icons.login),
          label: Text('Sign in with Gmail'),
          onPressed: _signIn,
        ),
      ),
    );
  }
}

class GoogleHttpClient extends http.BaseClient {
  final Map<String, String> _headers;
  final http.Client _client = http.Client();

  GoogleHttpClient(this._headers);

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) {
    return _client.send(request..headers.addAll(_headers));
  }

  @override
  void close() {
    _client.close();
  }
}
