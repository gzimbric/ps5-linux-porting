.PHONY: check manifests tests public-tree links

check: manifests tests public-tree links

manifests:
	python3 tools/validate_manifests.py

tests:
	python3 -m unittest discover -s tests -v

public-tree:
	python3 tools/check_public_tree.py

links:
	python3 tools/check_links.py
