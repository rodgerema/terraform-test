# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Terraform drift detection GitHub Action with automated monitoring
- Support for multiple environments (dev, staging, prod)
- Automated GitHub issue creation when drift is detected
- Teams webhook integration for notifications
- Duplicate drift detection prevention using content hashing

### Changed
- **2025-12-04**: Improved GitHub issue creation error handling
  - Enhanced error reporting with exit code validation
  - Made label assignment non-blocking to prevent failures when labels don't exist
  - Added clear success/error messages with issue URL capture

### Fixed
- **2025-12-04**: Fixed drift detection action to handle repositories without predefined labels
- Previous commits: Fixed environment selection and general stability issues

## [1.0.0] - Initial Release

### Added
- Basic Terraform infrastructure setup
- Multi-environment support (dev, staging, prod)
- AWS backend configuration
- GitHub Actions workflow structure
