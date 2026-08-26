import argparse
import sys
import json
from .sandbox import Sandbox
from .types import SandboxBackend
from .policy import PolicyValidator

def main():
    parser = argparse.ArgumentParser(description="swarmsandbox CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run a command in a sandbox")
    run_parser.add_argument("cmd", nargs="+", help="Command to run")
    run_parser.add_argument("--backend", choices=["auto", "subprocess", "container", "windows", "linux"], 
                            default="auto", help="Sandbox backend to use")
    
    # Policy check command
    check_parser = subparsers.add_parser("policy-check", help="Check sandbox policy")
    
    # Inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect sandbox capabilities")
    
    args = parser.parse_args()
    
    if args.command == "run":
        backend_map = {
            "auto": SandboxBackend.AUTO,
            "subprocess": SandboxBackend.SUBPROCESS,
            "container": SandboxBackend.CONTAINER,
            "windows": SandboxBackend.JOB_OBJECT,
            "linux": SandboxBackend.NAMESPACE
        }
        
        sandbox = Sandbox(backend=backend_map[args.backend])
        result = sandbox.run_sync(args.cmd)
        print(f"Exit Code: {result.exit_code}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        print("--- STDOUT ---")
        print(result.stdout)
        if result.stderr:
            print("--- STDERR ---")
            print(result.stderr)
        
        sys.exit(result.exit_code)
        
    elif args.command == "policy-check":
        policy = PolicyValidator.default_policy()
        warnings = PolicyValidator.validate(policy)
        if warnings:
            print("Warnings found in default policy:")
            for w in warnings:
                print(f"- {w}")
        else:
            print("Default policy is valid.")
            
    elif args.command == "inspect":
        print("Sandbox capabilities on this system:")
        import platform
        print(f"OS: {platform.system()}")
        print("Backends supported gracefully: AUTO, SUBPROCESS, JOB_OBJECT, NAMESPACE, CONTAINER")

if __name__ == "__main__":
    main()
