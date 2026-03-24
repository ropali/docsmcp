from dataclasses import dataclass
from bs4 import BeautifulSoup


@dataclass
class DetectionResult:
    needs_js: bool
    reason: str
    content_score: float  # 0.0 - 1.0, higher = more content found


class JSRenderDetector:
    """
    Analyzes raw HTML to determine if JS rendering is needed
    to get meaningful content out of a page.
    """

    # Frameworks that always need JS rendering
    JS_FRAMEWORK_SIGNALS = [
        # React / Next.js
        '<div id="__next"',
        '<div id="root"',
        # Nuxt / Vue
        '<div id="__nuxt"',
        '<div id="app"',
        # Docusaurus (popular for docs)
        "docusaurus",
        # Gatsby
        "___gatsby",
        # Angular
        "ng-version=",
    ]

    # Meta tags that indicate JS-rendered content
    JS_META_SIGNALS = [
        'name="fragment"',  # old escaped fragment pattern
        "data-react-helmet",
    ]

    # If the page body has less than this many visible words, suspect JS rendering
    MIN_WORD_COUNT = 50

    # If <script> tags outweigh <p>/<li>/<h1-h6> tags by this ratio, suspect JS
    SCRIPT_TO_CONTENT_RATIO_THRESHOLD = 3.0

    def analyze(self, html: str) -> DetectionResult:
        """
        Run all heuristics and return a DetectionResult.
        Stops at the first strong signal to avoid redundant work.
        """
        soup = BeautifulSoup(html, "html.parser")

        # framework fingerprinting
        raw_html_lower = html.lower()

        for signal in self.JS_FRAMEWORK_SIGNALS:
            if signal.lower() in raw_html_lower:
                return DetectionResult(
                    needs_js=True,
                    reason=f"JS framework detected: '{signal}'",
                    content_score=0.0,
                )

        for signal in self.JS_META_SIGNALS:
            if signal.lower() in raw_html_lower:
                return DetectionResult(
                    needs_js=True,
                    reason=f"JS meta signal detected: '{signal}'",
                    content_score=0.0,
                )

        # Content volume check
        score, word_count = self._content_score(soup)

        if word_count < self.MIN_WORD_COUNT:
            return DetectionResult(
                needs_js=True,
                reason=f"Too little visible text ({word_count} words < {self.MIN_WORD_COUNT})",
                content_score=score,
            )

        # Script-to-content ratio
        ratio = self._script_ratio(soup)
        if ratio > self.SCRIPT_TO_CONTENT_RATIO_THRESHOLD:
            return DetectionResult(
                needs_js=True,
                reason=f"High script-to-content ratio ({ratio:.1f})",
                content_score=score,
            )

        return DetectionResult(
            needs_js=False,
            reason="Sufficient static content found",
            content_score=score,
        )

    def _content_score(self, soup: BeautifulSoup) -> tuple[float, int]:
        """
        Count meaningful visible words in content tags.
        Returns (normalized_score, raw_word_count).
        """
        # Remove noise elements first
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()

        content_tags = soup.find_all(
            ["p", "li", "h1", "h2", "h3", "h4", "td", "article"]
        )
        text = " ".join(tag.get_text(separator=" ") for tag in content_tags)
        words = [w for w in text.split() if len(w) > 2]  # skip "a", "to", etc.
        word_count = len(words)

        # Normalize: 500+ words = full score
        score = min(word_count / 500.0, 1.0)
        return score, word_count

    def _script_ratio(self, soup: BeautifulSoup) -> float:
        """Ratio of <script> tags to meaningful content tags."""
        script_count = len(soup.find_all("script"))
        content_count = len(
            soup.find_all(["p", "li", "h1", "h2", "h3", "h4", "article"])
        )
        if content_count == 0:
            return float(script_count)  # all scripts, no content = very high ratio

        return script_count / content_count
