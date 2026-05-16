# Makefile for Hybrid Test Infrastructure

.PHONY: help install setup provision run-tests clean destroy

help:
	@echo "Hybrid Test Infrastructure - Available Commands:"
	@echo ""
	@echo "  make install     - Install Python dependencies"
	@echo "  make setup       - Initialize configuration"
	@echo "  make provision   - Provision infrastructure with Terraform"
	@echo "  make run-tests   - Run all tests with orchestrator"
	@echo "  make unit        - Run unit tests only"
	@echo "  make integration - Run integration tests only"
	@echo "  make performance - Run performance tests only"
	@echo "  make clean       - Clean up test results"
	@echo "  make destroy     - Destroy all infrastructure"
	@echo ""

install:
	@echo "Installing Python dependencies..."
	pip install -r orchestrator/requirements.txt
	pip install -r tests/requirements.txt

setup:
	@echo "Setting up configuration..."
	@if [ ! -f orchestrator/config.yml ]; then \
		cp orchestrator/config.example.yml orchestrator/config.yml; \
		echo "Created orchestrator/config.yml - please customize it"; \
	else \
		echo "Configuration already exists"; \
	fi

provision:
	@echo "Provisioning infrastructure with Terraform..."
	cd terraform && terraform init
	cd terraform && terraform plan
	cd terraform && terraform apply -auto-approve

run-tests:
	@echo "Running all tests with orchestrator..."
	cd orchestrator && python main.py --suite all --optimize-cost

unit:
	@echo "Running unit tests on cloud spot instances..."
	cd orchestrator && python main.py --suite unit --target cloud-spot

integration:
	@echo "Running integration tests on Azure AKS..."
	cd orchestrator && python main.py --suite integration --target azure-aks

performance:
	@echo "Running performance tests on HCI..."
	cd orchestrator && python main.py --suite performance --target hci

clean:
	@echo "Cleaning up test results..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name "*.log" -delete
	find . -name "results-*.xml" -delete
	rm -rf orchestrator/*.log

destroy:
	@echo "WARNING: This will destroy all provisioned infrastructure!"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ]
	cd terraform && terraform destroy -auto-approve
