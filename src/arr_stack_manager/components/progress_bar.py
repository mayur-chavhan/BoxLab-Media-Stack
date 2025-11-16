"""Enhanced progress bar widget with detailed status display."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, ProgressBar


class EnhancedProgressBar(Container):
    """An enhanced progress bar with title, status message, and percentage display."""

    DEFAULT_CSS = """
    EnhancedProgressBar {
        height: auto;
        width: 100%;
        padding: 1;
        background: $surface;
        border: solid $primary;
    }

    EnhancedProgressBar .progress-header {
        height: auto;
        width: 100%;
        margin-bottom: 1;
    }

    EnhancedProgressBar .progress-title {
        text-style: bold;
        color: $text;
        width: 1fr;
    }

    EnhancedProgressBar .progress-percentage {
        color: $accent;
        text-style: bold;
        width: auto;
    }

    EnhancedProgressBar .progress-bar-container {
        height: 1;
        width: 100%;
        margin-bottom: 1;
    }

    EnhancedProgressBar ProgressBar {
        width: 100%;
    }

    EnhancedProgressBar .progress-status {
        height: auto;
        width: 100%;
        color: $text-muted;
    }

    EnhancedProgressBar .progress-details {
        height: auto;
        width: 100%;
        margin-top: 1;
        color: $text-muted;
    }

    EnhancedProgressBar.complete {
        border: solid $success;
    }

    EnhancedProgressBar.complete .progress-title {
        color: $success;
    }

    EnhancedProgressBar.error {
        border: solid $error;
        background: $error 10%;
    }

    EnhancedProgressBar.error .progress-title {
        color: $error;
    }
    """

    def __init__(
        self,
        title: str,
        total: float = 100.0,
        show_percentage: bool = True,
        show_eta: bool = False,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the enhanced progress bar.

        Args:
            title: Title to display above the progress bar
            total: Total value for progress (default 100 for percentage)
            show_percentage: Whether to show percentage display
            show_eta: Whether to show estimated time remaining
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.title = title
        self.total = total
        self.show_percentage = show_percentage
        self.show_eta = show_eta
        self._progress = 0.0
        self._status_message = ""
        self._details = ""

    def compose(self) -> ComposeResult:
        """Compose the progress bar layout."""
        # Header with title and percentage
        with Horizontal(classes="progress-header"):
            yield Label(self.title, classes="progress-title", id="progress-title")
            if self.show_percentage:
                yield Label(
                    self._format_percentage(), classes="progress-percentage", id="progress-pct"
                )

        # Progress bar
        with Vertical(classes="progress-bar-container"):
            yield ProgressBar(total=self.total, show_eta=self.show_eta, id="progress-bar")

        # Status message
        yield Label(self._status_message, classes="progress-status", id="progress-status")

        # Additional details
        if self._details:
            yield Label(self._details, classes="progress-details", id="progress-details")

    def update_progress(
        self, progress: float, status: str | None = None, details: str | None = None
    ) -> None:
        """Update the progress bar.

        Args:
            progress: Current progress value (0 to total)
            status: Optional status message to display
            details: Optional additional details to display
        """
        self._progress = min(progress, self.total)

        if status is not None:
            self._status_message = status

        if details is not None:
            self._details = details

        if self.is_mounted:
            # Update progress bar
            progress_bar = self.query_one("#progress-bar", ProgressBar)
            progress_bar.update(progress=self._progress)

            # Update percentage
            if self.show_percentage:
                pct_label = self.query_one("#progress-pct", Label)
                pct_label.update(self._format_percentage())

            # Update status
            status_label = self.query_one("#progress-status", Label)
            status_label.update(self._status_message)

            # Update details if present
            if self._details:
                try:
                    details_label = self.query_one("#progress-details", Label)
                    details_label.update(self._details)
                except Exception:
                    # Details label might not exist yet
                    pass

            # Update styling based on completion
            if self._progress >= self.total:
                self.add_class("complete")

    def set_error(self, error_message: str) -> None:
        """Set the progress bar to error state.

        Args:
            error_message: Error message to display
        """
        self.add_class("error")
        self._status_message = f"✗ {error_message}"

        if self.is_mounted:
            status_label = self.query_one("#progress-status", Label)
            status_label.update(self._status_message)

    def set_complete(self, message: str = "Complete") -> None:
        """Set the progress bar to complete state.

        Args:
            message: Completion message to display
        """
        self._progress = self.total
        self._status_message = f"✓ {message}"
        self.add_class("complete")

        if self.is_mounted:
            progress_bar = self.query_one("#progress-bar", ProgressBar)
            progress_bar.update(progress=self.total)

            if self.show_percentage:
                pct_label = self.query_one("#progress-pct", Label)
                pct_label.update("100%")

            status_label = self.query_one("#progress-status", Label)
            status_label.update(self._status_message)

    def reset(self) -> None:
        """Reset the progress bar to initial state."""
        self._progress = 0.0
        self._status_message = ""
        self._details = ""
        self.remove_class("complete", "error")

        if self.is_mounted:
            progress_bar = self.query_one("#progress-bar", ProgressBar)
            progress_bar.update(progress=0.0)

            if self.show_percentage:
                pct_label = self.query_one("#progress-pct", Label)
                pct_label.update("0%")

            status_label = self.query_one("#progress-status", Label)
            status_label.update("")

    def _format_percentage(self) -> str:
        """Format the current progress as a percentage."""
        if self.total == 0:
            return "0%"
        percentage = (self._progress / self.total) * 100
        return f"{percentage:.0f}%"

    @property
    def progress(self) -> float:
        """Get the current progress value."""
        return self._progress

    @property
    def is_complete(self) -> bool:
        """Check if progress is complete."""
        return self._progress >= self.total

    @property
    def percentage(self) -> float:
        """Get the current progress as a percentage (0-100)."""
        if self.total == 0:
            return 0.0
        return (self._progress / self.total) * 100
