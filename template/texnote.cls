\NeedsTeXFormat{LaTeX2e}

\ProvidesClass{texnote}
\LoadClass{article} 
\RequirePackage{amsthm}
\RequirePackage{amssymb}
\RequirePackage{mathrsfs}
\RequirePackage{tikz-cd}

\RequirePackage{amsmath}

\RequirePackage{xr-hyper} 
%hyperlinks and referencing
\RequirePackage{hyperref} 
\RequirePackage[capitalize,nameinlink,noabbrev]{cleveref}


%setup external file links

\RequirePackage{import}
\ifx\HCode\UnDeFiNeD
    \subimport{../notes}{documents.tex}
\fi

\RequirePackage{slashed}

%setup geometry
\RequirePackage{geometry}
\RequirePackage{graphicx}
\graphicspath{{../resources}}



\RequirePackage[style=alphabetic]{biblatex}
\addbibresource{../bibliography.bib}


\hypersetup{
    colorlinks = true,
    citecolor = cyan
}

\theoremstyle{definition}

\newtheorem{definition}{Definition}

\newtheorem{example}[definition]{Example}
\newtheorem{prop}[definition]{Proposition}
\newtheorem{lemma}[definition]{Lemma}
\newtheorem{thm}[definition]{Theorem}
\newtheorem{cor}[definition]{Corollary}
\newtheorem{rmk}[definition]{Remark}
\newtheorem{conj}[definition]{Conjecture}

\usepackage{ifthen}

%TeXNotes Commands
\newcommand{\excref}[2][note]
    {\ifthenelse{\equal{#1}{note}}
    {\hyperref[#2-#1]{\texttt{#2}}}
    {\hyperref[#2-#1]{\texttt{#2/}\cref{#2-#1}}}}
\newcommand{\exhyperref}[3][note]{\hyperref[#2-#1]{#3}}

\newcommand{\transclude}[2][note]{\ExecuteMetaData[../notes/slipbox/#2.tex]{#1}}

\usepackage{catchfilebetweentags}

%currentdoc command for make4ht fix 
\makeatletter
\newcommand\currentdoc[1]{\edef\@currentlabel{#1}\label{#1}}
\makeatother

\ProcessOptions

