.PHONY: build scan extract unknown-merchants categorize report shell clean

IMAGE_NAME := financial-advisor:latest

DOCKER := $(shell if groups | grep -q docker; then echo "docker"; else echo "sudo docker"; fi)

# Build the Docker image (network allowed — fetches packages once)
build:
	@echo "Building Docker image..."
	$(DOCKER) build -t $(IMAGE_NAME) .

# Scan for HIGH/CRITICAL vulnerabilities before committing
scan:
	@echo "Scanning image for vulnerabilities..."
	$(DOCKER) run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy:latest image --severity HIGH,CRITICAL $(IMAGE_NAME)

# Extract transactions from ~/financials/data/ → ~/financials/transactions.json
# Network isolated: no outbound connections during processing
extract:
	@echo "Extracting transactions (network=none)..."
	$(DOCKER) run --rm --network=none \
		-v $(HOME)/financials/data:/data:ro \
		-v $(HOME)/financials:/reports \
		$(IMAGE_NAME) fa-extract

# List merchants with no matching category rule → ~/financials/unknown_merchants.json
unknown-merchants:
	@echo "Finding uncategorized merchants (network=none)..."
	$(DOCKER) run --rm --network=none \
		-v $(HOME)/financials:/reports \
		$(IMAGE_NAME) fa-unknown-merchants

# Generate monthly budget report → ~/financials/YYYY-MM_budget.md (defaults to last complete month)
# Override month with: make report MONTH=2026-03
report:
	@echo "Generating budget report (network=none)..."
	$(DOCKER) run --rm --network=none \
		-v $(HOME)/financials:/reports \
		$(IMAGE_NAME) fa-report $(MONTH)

# Apply categories.json rules to all transactions → ~/financials/categorized_transactions.json
categorize:
	@echo "Categorizing transactions (network=none)..."
	$(DOCKER) run --rm --network=none \
		-v $(HOME)/financials:/reports \
		$(IMAGE_NAME) fa-categorize

# Interactive shell for debugging (still network isolated)
shell:
	@echo "Entering container shell..."
	$(DOCKER) run --rm -it --network=none \
		-v $(HOME)/financials/data:/data:ro \
		-v $(HOME)/financials:/reports \
		$(IMAGE_NAME) /bin/bash

# Remove the built image
clean:
	@echo "Removing image..."
	$(DOCKER) rmi $(IMAGE_NAME) || true
