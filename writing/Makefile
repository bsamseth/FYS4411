# You want latexmk to *always* run, because make does not have all the info.
# Also, include non-file targets in .PHONY so they are run regardless of any
# file of the given name existing.
.PHONY: Thesis.pdf all clean

MAIN=Thesis
TEXFILES= Appendix.tex Introduction.tex MachineLearning.tex MergingVMCandML.tex MonteCarlo.tex QuantumTheory.tex Results.tex Thesis.tex VariationalMonteCarlo.tex commands.tex packages.tex

all: ${MAIN}.pdf

# Compile if needed.
${MAIN}.pdf: ${MAIN}.tex ${TEXFILES} preamble.sty
	latexmk -bibtex -f -pdf -pdflatex="pdflatex -synctex=1 -interaction=nonstopmode" $<

# Compile _and_ watch for future changes.
watch:
	latexmk -bibtex -pvc -f -pdf -pdflatex="pdflatex -synctex=1 -interaction=nonstopmode" ${MAIN}.tex

clean:
	latexmk -CA
	rm -f ${MAIN}.run.xml ${MAIN}.bbl *.fls
	rm -fr _region_.* auto prv_*.fmt
