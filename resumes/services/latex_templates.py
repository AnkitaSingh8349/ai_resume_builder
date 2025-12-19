MODERN_TEMPLATE = r"""
\documentclass{article}
\begin{document}

\begin{center}
{\Huge \textbf{%(full_name)s}} \\
%(email)s | %(phone)s
\end{center}

\section*{Summary}
%(summary)s

\section*{Skills}
%(skills)s

\section*{Experience}
%(experience)s

\section*{Education}
%(education)s

\end{document}
"""

CLASSIC_TEMPLATE = r"""
\documentclass{article}
\begin{document}

Name: %(full_name)s \\
Email: %(email)s \\
Phone: %(phone)s

\section*{Summary}
%(summary)s

\section*{Skills}
%(skills)s

\section*{Experience}
%(experience)s

\section*{Education}
%(education)s

\end{document}
"""
