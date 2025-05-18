import re
import json
import threading
import java.awt.event
from javax.swing import (
    JPanel, JTextArea, JButton, JScrollPane, JTextField, JComboBox, JLabel,
    JMenuItem, SwingWorker
)
from java.awt import BorderLayout, GridLayout
from burp import IBurpExtender, IContextMenuFactory, IContextMenuInvocation, ITab
import os


class BurpExtender(IBurpExtender, IContextMenuFactory, ITab):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        self._stdout = callbacks.getStdout()
        self._callbacks.setExtensionName("Regex Extractor")

        self.pattern_file = os.path.join(os.getcwd(), "saved_regex_patterns.json")
        self.regex_patterns = self.load_regex_patterns()

        self.init_gui()
        self._callbacks.registerContextMenuFactory(self)

    def init_gui(self):
        self.tab = JPanel(BorderLayout())

        input_panel = JPanel(GridLayout(4, 1))
        self.name_input = JTextField()
        input_panel.add(JLabel("Pattern Name:"))
        input_panel.add(self.name_input)

        self.regex_input = JTextArea(3, 20)
        self.regex_input.setLineWrap(True)
        self.regex_input.setWrapStyleWord(True)
        input_panel.add(JLabel("Regex Pattern:"))
        input_panel.add(JScrollPane(self.regex_input))

        self.save_button = JButton("Save Pattern", actionPerformed=self.save_pattern)
        self.load_button = JButton("Load Patterns", actionPerformed=self.load_patterns)
        self.pattern_dropdown = JComboBox(self.regex_patterns.keys())
        self.pattern_dropdown.addActionListener(self.on_pattern_selected)

        self.output_area = JTextArea(20, 50)
        self.output_area.setEditable(False)
        scroll_pane = JScrollPane(self.output_area)

        control_panel = JPanel()
        control_panel.add(self.save_button)
        control_panel.add(self.load_button)
        control_panel.add(JLabel("Saved Patterns:"))
        control_panel.add(self.pattern_dropdown)

        self.tab.add(input_panel, BorderLayout.NORTH)
        self.tab.add(control_panel, BorderLayout.CENTER)
        self.tab.add(scroll_pane, BorderLayout.SOUTH)

        self._callbacks.addSuiteTab(self)

    def getTabCaption(self):
        return "Regex Extractor"

    def getUiComponent(self):
        return self.tab

    def load_regex_patterns(self):
        try:
            with open(self.pattern_file, "r") as f:
                patterns = json.load(f)
                if not isinstance(patterns, dict):
                    self.append_output("Pattern file format is invalid.\n")
                    return {}
                return patterns
        except Exception as e:
            self.append_output("Failed to load regex patterns: {}\n".format(e))
            return {}

    def save_pattern(self, event):
        name = self.name_input.getText().strip()
        pattern = self.regex_input.getText().strip()

        if not name or not pattern:
            self.append_output("Please enter both name and regex pattern.\n")
            return

        self.regex_patterns[name] = pattern
        try:
            with open(self.pattern_file, "w") as f:
                json.dump(self.regex_patterns, f, indent=4)
        except Exception as e:
            self.append_output("Error saving pattern: {}\n".format(e))
            return

        if name not in [self.pattern_dropdown.getItemAt(i) for i in range(self.pattern_dropdown.getItemCount())]:
            self.pattern_dropdown.addItem(name)

        self.append_output("Pattern '{}' saved successfully.\n".format(name))

    def load_patterns(self, event):
        new_patterns = self.load_regex_patterns()
        if not new_patterns:
            return

        self.regex_patterns = new_patterns

        self.pattern_dropdown.removeAllItems()
        for name in sorted(self.regex_patterns.keys()):
            self.pattern_dropdown.addItem(name)

        self.append_output("Patterns reloaded from saved_regex_patterns.json.\n")

    def on_pattern_selected(self, event):
        selected_name = self.pattern_dropdown.getSelectedItem()
        if selected_name in self.regex_patterns:
            self.regex_input.setText(self.regex_patterns[selected_name])
            self.name_input.setText(selected_name)

    def createMenuItems(self, invocation):
        menu_item = JMenuItem("Extract Regex Matches from Responses")
        menu_item.addActionListener(MenuItemActionListener(self, invocation))
        return [menu_item]

    def extract_regex_from_responses(self, invocation):
        selected_items = invocation.getSelectedMessages()
        if not selected_items:
            self.append_output("No requests selected.\n")
            return

        selected_name = self.pattern_dropdown.getSelectedItem()
        regex_pattern = self.regex_patterns.get(selected_name, "")

        if not regex_pattern:
            self.append_output("No regex pattern selected.\n")
            return

        try:
            compiled_pattern = re.compile(regex_pattern)
        except re.error as e:
            self.append_output("Regex compile error: {}\n".format(e))
            return

        self.append_output("Processing {} responses...\n".format(len(selected_items)))

        class ExtractWorker(SwingWorker):
            def doInBackground(inner_self):
                seen_lengths = set()
                unique_messages = []

                for message in selected_items:
                    response = message.getResponse()
                    if response:
                        length = len(response)
                        if length not in seen_lengths:
                            seen_lengths.add(length)
                            unique_messages.append(message)

                response_matches = set()
                for message in unique_messages:
                    try:
                        response_str = self._helpers.bytesToString(message.getResponse())
                        local_matches = compiled_pattern.findall(response_str)
                        response_matches.update(local_matches)
                    except Exception as e:
                        self.append_output("Error processing a response: {}\n".format(e))

                return response_matches, len(unique_messages)

            def done(inner_self):
                try:
                    matches, unique_count = inner_self.get()
                    self.append_output("Unique responses processed: {}\n".format(unique_count))
                    if matches:
                        self.append_output("--- Matches from Responses ---\n")
                        self.append_output("\n".join(sorted(matches)) + "\n")
                    else:
                        self.append_output("No matches found in the responses.\n")
                except Exception as e:
                    self.append_output("Error retrieving matches: {}\n".format(e))

        ExtractWorker().execute()

    def append_output(self, text):
        self.output_area.append(text)
        self.output_area.setCaretPosition(self.output_area.getDocument().getLength())


class MenuItemActionListener(java.awt.event.ActionListener):
    def __init__(self, extender, invocation):
        self.extender = extender
        self.invocation = invocation

    def actionPerformed(self, event):
        self.extender.extract_regex_from_responses(self.invocation)
