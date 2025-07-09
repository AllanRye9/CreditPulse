import 'package:flutter/material.dart';

class SpendInsightsScreen extends StatelessWidget {
  final Map<String, List<Map<String, dynamic>>> monthlyData;

  SpendInsightsScreen({required this.monthlyData});

  double getTotalAmount(List<Map<String, dynamic>> transactions, {String type = 'Debit'}) {
    return transactions
        .where((txn) => txn['type'] == type)
        .fold(0.0, (sum, txn) => sum + (txn['amount'] ?? 0));
  }

  @override
  Widget build(BuildContext context) {
    final months = monthlyData.keys.toList();

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
              itemCount: months.length,
              itemBuilder: (context, index) {
                final month = months[index];
                final transactions = monthlyData[month]!;

                final totalDebit = getTotalAmount(transactions, type: 'Debit');
                final totalCredit = getTotalAmount(transactions, type: 'Credit');

                return Card(
                  elevation: 3,
                  margin: EdgeInsets.symmetric(vertical: 8),
                  child: ExpansionTile(
                    title: Text(
                      '$month - Debits: AED ${totalDebit.toStringAsFixed(2)} | Credits: AED ${totalCredit.toStringAsFixed(2)}',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    children: transactions.map((txn) {
                      return ListTile(
                        leading: Icon(
                          txn['type'] == 'Credit'
                              ? Icons.arrow_downward
                              : Icons.arrow_upward,
                          color: txn['type'] == 'Credit'
                              ? Colors.green
                              : Colors.red,
                        ),
                        title: Text('${txn['category']} - ${txn['type']}'),
                        subtitle: Text(txn['description']),
                        trailing: Text(
                          '${txn['currency']} ${txn['amount'].toStringAsFixed(2)}',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: txn['type'] == 'Credit' ? Colors.green : Colors.red,
                          ),
                        ),
                      );
                    }).toList(),
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
