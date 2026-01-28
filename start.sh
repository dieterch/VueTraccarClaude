# fresh compile at startup
python prepare.py
pushd ./frontend
npm install --no-audit --no-fund
npm run justbuild
popd
export PRODUCTION="1" 
python -OO app.py
