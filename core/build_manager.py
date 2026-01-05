"""Build process manager for sBitx Branch Manager"""

import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class BuildResult:
    """Result of a build operation"""
    success: bool
    returncode: int


class BuildError(Exception):
    """Build operation errors"""
    pass


class BuildManager:
    """Manages the sBitx build process"""

    @staticmethod
    def run_build(target_path: str) -> BuildResult:
        """
        Execute the sBitx build script

        Args:
            target_path: Path to sbitx directory (should be /home/pi/sbitx)

        Returns:
            BuildResult with build status

        Raises:
            BuildError: If build script doesn't exist or execution fails critically
        """
        build_script = Path(target_path) / 'build'

        # Check if build script exists
        if not build_script.exists():
            raise BuildError(
                f"Build script not found at {build_script}\n"
                "Make sure you're in the correct sBitx directory."
            )

        # Check if build script is executable
        if not build_script.is_file():
            raise BuildError(f"{build_script} is not a file")

        try:
            # Run the build command: ./build sbitx
            print("\n" + "="*60)
            print("=== Building sBitx (this may take several minutes) ===")
            print("="*60 + "\n")

            result = subprocess.run(
                ['./build', 'sbitx'],
                cwd=target_path,
                timeout=900  # 15 minutes max
            )

            print("\n" + "="*60)
            if result.returncode == 0:
                print("=== Build completed successfully ===")
            else:
                print(f"=== Build finished with exit code {result.returncode} ===")
            print("="*60 + "\n")

            # Consider successful if returncode is 0
            success = (result.returncode == 0)

            return BuildResult(
                success=success,
                returncode=result.returncode
            )

        except subprocess.TimeoutExpired:
            raise BuildError(
                "Build timeout after 15 minutes\n"
                "The build process is taking too long or may be stuck."
            )
        except Exception as e:
            raise BuildError(f"Failed to run build: {e}")

    @staticmethod
    def check_build_prerequisites(target_path: str) -> tuple[bool, str]:
        """
        Check if build prerequisites are met

        Args:
            target_path: Path to sbitx directory

        Returns:
            Tuple of (prerequisites_met, message)
        """
        issues = []

        # Check if directory exists
        if not Path(target_path).exists():
            issues.append(f"Directory {target_path} does not exist")

        # Check if build script exists
        build_script = Path(target_path) / 'build'
        if not build_script.exists():
            issues.append(f"Build script not found at {build_script}")

        # Check for Makefile
        makefile = Path(target_path) / 'Makefile'
        if not makefile.exists():
            issues.append(f"Makefile not found at {makefile}")

        if issues:
            return False, "\n".join(issues)

        return True, "All prerequisites met"

    @staticmethod
    def clean_build(target_path: str) -> BuildResult:
        """
        Run 'make clean' before building

        Args:
            target_path: Path to sbitx directory

        Returns:
            BuildResult with clean operation status
        """
        try:
            print("\n=== Running make clean ===")
            result = subprocess.run(
                ['make', 'clean'],
                cwd=target_path,
                timeout=60
            )

            if result.returncode == 0:
                print("=== Clean completed successfully ===\n")
            else:
                print(f"=== Clean finished with exit code {result.returncode} ===\n")

            return BuildResult(
                success=result.returncode == 0,
                returncode=result.returncode
            )

        except subprocess.TimeoutExpired:
            raise BuildError("Clean timeout after 60 seconds")
        except Exception as e:
            raise BuildError(f"Failed to run clean: {e}")
