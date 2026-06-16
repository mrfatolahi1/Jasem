"""Reading and writing the padded Markdown tables jasem stores data in."""

import os


def sanitize(text):
    """Return ``text`` made safe for a Markdown table cell.

    Pipes would break the column layout and newlines would split a row, so both
    are replaced.

    Args:
        text: Raw cell text.

    Returns:
        The sanitised, stripped text.
    """
    return text.replace("|", "/").replace("\n", " ").strip()


class MarkdownTable:
    """Renders and parses a fixed-column Markdown table backed by a file."""

    def __init__(self, path, columns, preamble):
        """Configure the table.

        Args:
            path: Filesystem path of the Markdown file.
            columns: Ordered column headers.
            preamble: Text written above the table (title and editing note).
        """
        self.path = path
        self.columns = columns
        self.preamble = preamble

    def read(self):
        """Return the table's data rows as lists of cell strings.

        Header and separator rows are skipped. Returns an empty list when the
        file does not exist.
        """
        if not os.path.exists(self.path):
            return []
        rows = []
        with open(self.path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line.startswith("|"):
                    continue
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                if len(cells) < len(self.columns):
                    continue
                if cells[0] == self.columns[0] or set(cells[0]) <= set("-: "):
                    continue
                rows.append(cells)
        return rows

    def write(self, rows):
        """Write ``rows`` aligned beneath the column headers.

        The parent directory is created if needed.

        Args:
            rows: Sequence of rows, each a sequence of cell strings matching the
                column count.
        """
        table = [list(self.columns), ["-" * len(name) for name in self.columns]]
        table.extend(list(row) for row in rows)
        widths = [max(len(row[index]) for row in table) for index in range(len(self.columns))]
        lines = []
        for position, row in enumerate(table):
            if position == 1:
                cells = ("-" * widths[index] for index in range(len(self.columns)))
            else:
                cells = (row[index].ljust(widths[index]) for index in range(len(self.columns)))
            lines.append("| " + " | ".join(cells) + " |")
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write(self.preamble + "\n".join(lines) + "\n")
