clean:
	@find . -name "*.pyc" -delete

deps:
	@echo "Installing deps"
	@pip install -r test-requirements.txt

ptest: clean deps
	@echo "Running tests"
	@py.test -s .
	@flake8 .

get:
	@/bin/echo "Installing test dependencies... "
	@go list -f '{{range .TestImports}}{{.}} {{end}}' ./... | tr ' ' '\n' |\
		grep '^.*\..*/.*$$' | grep -v 'github.com/globocom/tsuru-unit-agent' |\
		sort | uniq | xargs go get -u >/dev/null 2>&1

	@/bin/echo "Installing production dependencies... "
	@go list -f '{{range .Imports}}{{.}} {{end}}' ./... | tr ' ' '\n' |\
		grep '^.*\..*/.*$$' | grep -v 'github.com/globocom/tsuru-unit-agent' |\
		sort | uniq | xargs go get -u >/dev/null 2>&1

	@/bin/echo "ok"
test:
	@go test ./...
