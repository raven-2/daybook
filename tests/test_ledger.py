import os
import unittest
from datetime import datetime

from daybook.Ledger import Ledger
from daybook.Account import Account
from daybook.Transaction import Transaction


pcurr = 'dollars'
resources = '{}/resources'.format(os.path.dirname(__file__))


class TestLedger(unittest.TestCase):

    def test_single_transaction(self):
        """ Verify correct behavior for single csv.
        """
        ledger = Ledger(pcurr, hintsini='{}/hints.ini'.format(resources))
        ledger.loadCsv('{}/single.csv'.format(resources))

        src = ledger.accounts['my-employer']
        dest = ledger.accounts['my-checking']
        t = ledger.transactions[0]

        self.assertEqual(2, len(ledger.accounts))

        self.assertEqual('my-employer', src.name)
        self.assertEqual('income', src.type)
        self.assertEqual(-100, src.balances['dollars'])

        self.assertEqual('my-checking', dest.name)
        self.assertEqual('asset', dest.type)
        self.assertEqual(100, dest.balances['dollars'])

        self.assertTrue('paystub' in t.tags)
        self.assertEqual(t.src, src)
        self.assertEqual(t.dest, dest)
        self.assertEqual(t.date, datetime(2019, 10, 8))

    def test_hints_match(self):
        """ Verify that account names can be inferred from hints.
        """
        ledger = Ledger(pcurr, hintsini='{}/hints.ini'.format(resources))
        ledger.loadCsv('{}/single-hints/my-checking.csv'.format(resources))

        self.assertTrue('void' in ledger.accounts)
        self.assertTrue('my-checking' in ledger.accounts)
        self.assertTrue('grocery' in ledger.accounts)

        src = ledger.accounts['my-checking']
        dest = ledger.accounts['grocery']

        self.assertEqual(src.balances['dollars'], -45.77)
        self.assertEqual(dest.balances['dollars'], 45.77)

        self.assertEqual(src.type, 'asset')
        self.assertEqual(dest.type, 'expense')

    def test_bad_csv(self):
        """ A csv with a row that cannot suggest an account should error.

        The ledger should also remain unaffected by that csv entirely.
        """
        ledger = Ledger(pcurr)
        with self.assertRaises(ValueError):
            ledger.loadCsv('{}/badsrc.csv'.format(resources))

        self.assertEqual(0, len(ledger.accounts))
        self.assertEqual(0, len(ledger.transactions))

    def test_this_substitution(self):
        """Verify behavior for transactions on 'this'.

        Transactions that contain 'this' as the account name should
        substitute the basename of the csv.
        """
        ledger = Ledger(pcurr, hintsini='{}/hints.ini'.format(resources))
        ledger.loadCsv('{}/employer-payroll.csv'.format(resources))

        self.assertTrue('employer-payroll' in ledger.accounts)

        emp = ledger.accounts['employer-payroll']
        self.assertEqual('employer-payroll', emp.name)
        self.assertEqual('income', emp.type)
        self.assertEqual(-100, emp.balances['dollars'])

    def test_multiple_transactions(self):
        """ Multiple transactions from a single csv should zero
        """

        ledger = Ledger(pcurr, hintsini='{}/hints.ini'.format(resources))
        ledger.loadCsv('{}/loan-payoff.csv'.format(resources))

        self.assertEqual(4, len(ledger.accounts))
        self.assertEqual(5, len(ledger.transactions))

        for a in ['car-loan', 'void', 'my-company-payroll', 'my-checking']:
            self.assertTrue(a in ledger.accounts)
            ac = ledger.accounts[a]
            self.assertEqual(a, ac.name)

        s = sum([x.balances['dollars'] for y, x in ledger.accounts.items()])
        self.assertEqual(0, s)

    def test_multiple_csvs_redundant(self):
        """ Verify duplicated transactions across csvs.

        Transactions read from multiple csvs should not enter twice if
        those transactions have the same dates, src and destination account
        names, and identical amounts.
        """
        path = '{}/multi-csv'.format(resources)
        csvs = [
            '{}/car-loan.csv'.format(path),
            '{}/my-checking.csv'.format(path),
            '{}/my-company-payroll.csv'.format(path),
        ]

        ledger = Ledger(pcurr)
        ledger.loadCsvs(csvs)

        self.assertEqual(4, len(ledger.accounts))
        self.assertEqual(5, len(ledger.transactions))

    def test_multiple_csvs_tags(self):
        """ Tags from duplicate transactions should sum.
        """
        path = '{}/multi-csv-tags'.format(resources)
        csvs = [
            '{}/checking.csv'.format(path),
            '{}/employer-payroll.csv'.format(path),
        ]

        ledger = Ledger(pcurr)
        ledger.loadCsvs(csvs)

        expected = ['payment', 'tags', 'i', 'got', 'paid']

        self.assertEqual(len(expected), len(ledger.transactions[0].tags))
        for e in expected:
            self.assertTrue(e in ledger.transactions[0].tags)


if __name__ == '__main__':
    unittest.main()
