import 'package:flutter/material.dart';

class DashboardScreen extends StatelessWidget {
  final List<Map<String, String>> reminders;

  DashboardScreen({required this.reminders});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text('CreditPulse Dashboard'),
          bottom: TabBar(
            tabs: [
              Tab(text: 'Due Reminders'),
              Tab(text: 'Spend Insights'),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            DueRemindersScreen(reminders: reminders),
            SpendInsightsScreen(),
          ],
        ),
      ),
    );
  }
}

class DueRemindersScreen extends StatelessWidget {
  final List<Map<String, String>> reminders;

  DueRemindersScreen({required this.reminders});

  @override
  Widget build(BuildContext context) {
    if (reminders.isEmpty) {
      return Center(child: Text("No reminders found."));
    }

    return ListView.builder(
      padding: EdgeInsets.all(10),
      itemCount: reminders.length,
      itemBuilder: (context, index) {
        final item = reminders[index];
        return Card(
          elevation: 3,
          margin: EdgeInsets.symmetric(vertical: 8),
          child: ListTile(
            title: Text(item['card'] ?? ''),
            subtitle: Text(
              'Due: ${item['due']}\nAmount: ${item['amount']}',
              style: TextStyle(height: 1.5),
            ),
            trailing: Chip(
              label: Text(
                item['status'] ?? '',
                style: TextStyle(color: Colors.white),
              ),
              backgroundColor: (item['status'] == 'Paid')
                  ? Colors.green
                  : Colors.red,
            ),
          ),
        );
      },
    );
  }
}

class SpendInsightsScreen extends StatelessWidget {
  final List<Map<String, dynamic>> categories = [
    {'name': 'Food', 'amount': 620.0},
    {'name': 'Travel', 'amount': 1150.0},
    {'name': 'Shopping', 'amount': 800.0},
    {'name': 'EMI', 'amount': 300.0},
  ];

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(10.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Monthly Spend Breakdown',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          SizedBox(height: 10),
          Expanded(
            child: ListView.builder(
              itemCount: categories.length,
              itemBuilder: (context, index) {
                final item = categories[index];
                return Card(
                  elevation: 2,
                  margin: EdgeInsets.symmetric(vertical: 6),
                  child: ListTile(
                    leading: Icon(Icons.category_outlined),
                    title: Text(item['name']),
                    trailing: Text(
                      'AED ${item['amount'].toStringAsFixed(2)}',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
