
python -m venv .venv
%cd%\.venv\bin\activate.bat
pip install -r %cd%\requirements.txt
pyinstaller --clean %cd%\tatc.spec

COPY %cd%\LICENSE.txt %cd%\dist
COPY %cd%\README.txt %cd%\dist
COPY %cd%\examples %cd%\dist\examples
