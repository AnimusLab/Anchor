import sys

def supports_unicode():
    """Detect if the terminal supports UTF-8/Unicode."""
    try:
        # Check standard output encoding
        encoding = sys.stdout.encoding
        if encoding:
            return encoding.lower() in ('utf-8', 'utf-16', 'utf-32')
        return False
    except AttributeError:
        return False

# Symbol constants
if supports_unicode():
    ANCHOR_ICON  = "⚓"
    CHECK        = "✓"
    CROSS        = "✗"
    WARN         = "!"
    BAR          = "─"
    ARROW        = "→"
else:
    ANCHOR_ICON  = "[ANCHOR]"
    CHECK        = "OK"
    CROSS        = "X"
    WARN         = "!"
    BAR          = "-"
    ARROW        = "->"
