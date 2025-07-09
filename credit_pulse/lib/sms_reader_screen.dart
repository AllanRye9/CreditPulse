import 'package:flutter/material.dart';
import 'package:telephony/telephony.dart';
import 'spend_insights_screen.dart'; // import your screen

class SmsReaderScreen extends StatefulWidget {
  @override
  _SmsReaderScreenState createState() => _SmsReaderScreenState();
}

class _SmsReaderScreenState extends State<SmsReaderScreen> {
  final Telephony telephony = Telephony.instance;
  List<SmsMessage> messages = [];

  @override
  void initState() {
    super.initState();
    _getSmsMessages();
  }

  void _getSmsMessages() async {
    final bool? permissionsGranted = await telephony.requestPhoneAndSmsPermissions;
    if (permissionsGranted ?? false) {
      final List<SmsMessage> smsList = await telephony.getInboxSms(
        columns: [SmsColumn.ADDRESS, SmsColumn.BODY, SmsColumn.DATE],
        filter: SmsFilter.where(SmsColumn.BODY).like("%transaction%")
          .or(SmsColumn.BODY).like("%payment%")
          .or(SmsColumn.BODY).like("%credit%")
          .or(SmsColumn.BODY).like("%bill%")
          .or(SmsColumn.BODY).like("%spent%")
          .or(SmsColumn.BODY).like("%debited%"),
      );
      setState(() {
        messages = smsList;
      });
    }
  }

  void _viewInsights() {
    final data = _parseMessagesToSpendData(messages);

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => SpendInsightsScreen(monthlyData: data),
      ),
    );
  }

  Map<String, List<Map<String, dynamic>>> _parseMessagesToSpendData(List<SmsMessage> messages) {
    final Map<String, List<Map<String, dynamic>>> grouped = {};

    for (var msg in messages) {
      final body = msg.body?.toLowerCase() ?? '';
      final date = msg.date != null ? DateTime.fromMillisecondsSinceEpoch(msg.date!) : DateTime.now();
      final monthKey = "${_getMonthName(date.month)} ${date.year}";

      String category = 'Others';
      if (body.contains('uber') || body.contains('flight') || body.contains('taxi')) {
        category = 'Travel';
      } else if (body.contains('amazon') || body.contains('zara') || body.contains('mall') || body.contains('store')) {
        category = 'Shopping';
      } else if (body.contains('restaurant') || body.contains('kfc') || body.contains('food') || body.contains('pizza')) {
        category = 'Food';
      } else if (body.contains('emi') || body.contains('loan') || body.contains('instalment')) {
        category = 'EMI';
      }

      final amountRegex = RegExp(r'(AED|USD|INR)?\s?(\d{1,3}(,\d{3})*|\d+)(\.\d{2})?');
      final match = amountRegex.firstMatch(body);
      final amountStr = match?.group(0)?.replaceAll(RegExp(r'[^\d.]'), '') ?? '0';
      final amount = double.tryParse(amountStr) ?? 0;

      final description = (msg.body?.length ?? 0) > 40 ? '${msg.body!.substring(0, 40)}...' : msg.body ?? '';

      grouped.putIfAbsent(monthKey, () => []);
      grouped[monthKey]!.add({
        'category': category,
        'amount': amount,
        'description': description,
      });
    }

    return grouped;
  }

  String _getMonthName(int month) {
    const months = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ];
    return months[month - 1];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Credit SMS Insights"),
        actions: [
          if (messages.isNotEmpty)
            IconButton(
              icon: Icon(Icons.bar_chart),
              tooltip: "Spend Insights",
              onPressed: _viewInsights,
            ),
        ],
      ),
      body: messages.isEmpty
          ? Center(child: Text("No relevant SMS found."))
          : ListView.builder(
              itemCount: messages.length,
              itemBuilder: (context, index) {
                final msg = messages[index];
                return Card(
                  margin: EdgeInsets.all(8),
                  child: ListTile(
                    title: Text(msg.address ?? 'Unknown Sender'),
                    subtitle: Text(msg.body ?? ''),
                    trailing: Text(
                      DateTime.fromMillisecondsSinceEpoch(msg.date ?? 0)
                          .toString()
                          .split(' ')[0],
                      style: TextStyle(fontSize: 12),
                    ),
                  ),
                );
              },
            ),
    );
  }
}
