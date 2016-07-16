#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Converts EDS files to csv. Best approximation

author: Cornelis Dirk Haupt
website: https://www.linkedin.com/in/dirk-haupt-a1296316
last edited: July 2016
"""

import sys, os
from PyQt4 import QtGui
from PyQt4.QtGui import *
import csv

absDirPath = os.path.dirname(__file__)

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()

    def initUI(self):
        self.textEdit = QtGui.QTextEdit()
        self.setCentralWidget(self.textEdit)
        self.statusBar()

        self.setWindowIcon(QtGui.QIcon(os.path.join(absDirPath, "icons", "ICORDlogo.png")))
        openFile = QtGui.QAction(QtGui.QIcon('open.png'), 'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Convert EDS File')
        openFile.triggered.connect(self.eds_conversion)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)

        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('EDS Converter')
        self.show()

    def eds_conversion(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file',
                                                  '/home')

        lol = list(csv.reader(open(fname, 'rb'), delimiter='\t'))
        lol = [item for sublist in lol for item in sublist]
        my_data = [x.split("    ") for x in lol]
        my_data = [item for sublist in my_data for item in sublist]
        my_data = filter(None, my_data)
        # get rid of trailing whitespaces
        for ind in range(len(my_data)):
            my_data[ind] = my_data[ind].strip()

        # Remove all non-date numbers
        for ind in range(len(my_data)):
            if (len(my_data[ind]) < 6):
                try:
                    int(my_data[ind].replace(' ', ''))
                    print(
                    "Deleting " + str(my_data[ind]) + " at index " + str(ind) + " with len " + str(len(my_data[ind])))
                    my_data[ind] = ''
                except:
                    continue

        # Delete all empty elements
        my_data = [val for val in my_data if val != '']

        # Split all the end_dates correctly
        # dates are often replaced with 'U' or 'CON' for unknown reasons
        date_replacements = ['CON', 'U']
        ind = 0
        dates_counts = []
        end_date_inds = []
        end_date_found = False
        dates_count = 0

        for ind in range(len(my_data)):
            elem = my_data[ind]
            elem = elem.replace(' ', '')
            try:
                int(elem)
            except:
                if elem not in date_replacements:
                    end_date_found = False
                    if dates_count > 0:
                        dates_counts = dates_counts + [dates_count]
                        assert (len(dates_counts) == len(end_date_inds))
                        dates_count = 0
                    continue
            # Logically if you are here elem is an integer or in date_replacements
            if not end_date_found and len(elem) >= 6:
                end_date_inds = end_date_inds + [ind]
                end_date_found = True
                dates_count = 1
            else:
                if end_date_found and (len(elem) >= 6 or elem in date_replacements):
                    dates_count = dates_count + 1

        problem_inds = []
        # Concatenate end_dates properly
        for ind in range(len(end_date_inds)):
            date_elem = my_data[end_date_inds[ind]]
            date_elem = date_elem.replace(' ', '')
            date_count = dates_counts[ind]
            if date_count > 1:
                if (len(date_elem) / (date_count - 1)) < 6:
                    possible_date_concat = True
                    date_ind = end_date_inds[ind] + 1
                    add_on = ''
                    modifier = 2
                    while possible_date_concat:
                        add_on = add_on + my_data[date_ind]
                        if (date_count - modifier) <= 0:
                            print(
                            "Unsolvable problem at end_date " + date_elem + " at index " + str(end_date_inds[ind]) +
                            " skipping...")
                            problem_inds = problem_inds + [end_date_inds[ind]]
                            break
                        assert ((date_count - modifier) > 0)
                        if ((len(date_elem) + len(add_on)) / (date_count - modifier) == 6):
                            possible_date_concat = False
                            my_data[end_date_inds[ind]] = date_elem + add_on
                            for i in range(end_date_inds[ind] + 1, date_ind + 1):
                                my_data[i] = ''
                        date_ind = date_ind + 1
                        modifier = modifier + 1
                        if (ind + 1) < len(end_date_inds):
                            assert (
                            date_ind < end_date_inds[ind + 1])  # Otherwise you're overlapping with another date!

        my_data = [val for val in my_data if val != '']

        # Recompute date count but for start_dates
        # Recompute indices for end dates since you changed the array one line up
        # Find where the dates end in each case
        end_date_inds = []
        end_of_dates_inds = []
        start_dates_counts = []
        end_date_found = False
        start_dates_count = 0
        for ind in range(len(my_data)):
            elem = my_data[ind]
            elem = elem.replace(' ', '')
            try:
                int(elem)
            except:
                if elem not in date_replacements:
                    end_date_found = False
                    if start_dates_count > 0:
                        start_dates_counts = start_dates_counts + [start_dates_count - 1]
                        end_of_dates_inds = end_of_dates_inds + [ind]
                        assert (len(start_dates_counts) == len(end_date_inds) == len(end_of_dates_inds))
                        start_dates_count = 0
                    continue
            # Logically if you are here elem is an integer or in date_replacements
            if not end_date_found and len(elem) >= 6:
                end_date_inds = end_date_inds + [ind]
                end_date_found = True
                start_dates_count = 1
            else:
                if end_date_found and (len(elem) >= 6 or elem in date_replacements):
                    start_dates_count = start_dates_count + 1

        col_names = ['drug', 'end_date', 'start_date', 'dose', 'reason', 'conclusion']
        rows = [col_names]
        problem_rows = []
        # add drug, end_date, start_dates, doses, reasons and conclusion columns first
        for ind in range(len(end_date_inds)):
            problem_row = False
            start_ind = end_date_inds[ind]
            end_date_ind = end_date_inds[ind]
            start_date_count = start_dates_counts[ind]
            # Find the first drug for this set
            end_date = my_data[start_ind]
            if start_ind in problem_inds:
                problem_row = True
            for i in range(1, start_date_count + 1):
                start_ind = start_ind + i
                drug = my_data[end_date_ind - start_date_count + 1]
                row = []
                for j in range(start_ind, start_ind + (start_date_count * 4), start_date_count):
                    row = row + [my_data[j]]
                rows = rows + [[drug, end_date] + row]
                if problem_row:
                    problem_rows = problem_rows + [[(len(rows)-1)]]

        output_file_name = fname[:-4]
        output_file_name = output_file_name + '_csv.csv'
        with open(output_file_name, "wb") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        problems_file_name = fname[:-4]
        problems_file_name = problems_file_name + '_problem_rows.csv'
        with open(problems_file_name, "wb") as f:
            writer = csv.writer(f)
            writer.writerows(problem_rows)

        # Display output
        out_f = open(output_file_name, 'r')
        with out_f:
            data = out_f.read()
            self.textEdit.setText(data)
        w = QWidget()
        QMessageBox.information(w, "Conversion Complete", "csv saved to " + output_file_name)
        w = QWidget()
        QMessageBox.information(w, "Conversion Complete", "Problem rows saved to " + problems_file_name)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
    sys.exit(app.exec_())