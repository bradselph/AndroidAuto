# Contributing to Android Automation Tool

Thank you for considering contributing to Android Automation Tool! This document outlines the process for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.12 or higher
- PyQt5
- OpenCV
- Basic knowledge of Android ADB

### Setting Up Development Environment

1. Fork the repository
2. Clone your fork:
   ```
   git clone https://github.com/your-username/AndroidAuto.git
   cd AndroidAuto
   ```
3. Install development dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a branch for your changes:
   ```
   git checkout -b feature/your-feature-name
   ```

## Development Process

### Project Structure

- `controllers/`: Core functionality modules
- `drivers/`: ADB and scrcpy management
- `ui/`: PyQt5 interface components
- `utils/`: Helper functions and utilities
- `resources/`: Static resources like themes
- `main.py`: Application entry point


### Adding Features

1. Check the [Roadmap](ROADMAP.md) and existing issues to see what's planned
2. Update documentation if necessary

### Testing

- Run tests to ensure your changes don't break functionality

## Pull Request Process

1. Update your fork to include the latest changes from the upstream repository
2. Ensure your code follows the project's coding standards
3. Submit a pull request with a clear description of the changes
4. Link any relevant issues

## Pull Request Guidelines

- Document new features or behavior changes
- Update the README if necessary

## License

By contributing to this project, you agree that your contributions will be licensed under the project's [GNU AGPLv3 License](LICENSE).