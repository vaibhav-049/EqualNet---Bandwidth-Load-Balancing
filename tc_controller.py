import os
import platform
import shutil
import subprocess
from typing import Optional, List


class TcController:

    def __init__(
        self, iface: str = "eth0", default_rate: str = "1mbit"
    ) -> None:
        self.iface = iface
        self.default_rate = default_rate
        self.simulation = not (
            platform.system() == "Linux" and shutil.which("tc")
        )
        self.root_handle = "1:"
        self.default_class = "1:ff"

    def _run(self, args: List[str]) -> subprocess.CompletedProcess:
        if self.simulation:
            return subprocess.CompletedProcess(args=args, returncode=0)
        return subprocess.run(args, capture_output=True, text=True)

    def ensure_root_qdisc(self) -> None:
        if self.simulation:
            return
        subprocess.run(
            ["tc", "qdisc", "del", "dev", self.iface, "root"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._run(
            [
                "tc",
                "qdisc",
                "add",
                "dev",
                self.iface,
                "root",
                "handle",
                "1:",
                "htb",
                "default",
                "ff",
            ]
        )
        self._run(
            [
                "tc",
                "class",
                "add",
                "dev",
                self.iface,
                "parent",
                self.root_handle,
                "classid",
                self.default_class,
                "htb",
                "rate",
                self.default_rate,
                "ceil",
                self.default_rate,
            ]
        )

    def _classid_for_ip(self, ip: str) -> str:
        try:
            last = int(ip.split(".")[-1])
        except Exception:
            last = 1
        return f"1:{last:02x}"

    def set_limit(
        self, ip: str, rate_mbit: int, ceil_mbit: Optional[int] = None
    ) -> None:
        rate = f"{rate_mbit}mbit"
        ceil = f"{ceil_mbit}mbit" if ceil_mbit else rate
        classid = self._classid_for_ip(ip)
        if not self.simulation:
            subprocess.run(
                [
                    "tc",
                    "class",
                    "del",
                    "dev",
                    self.iface,
                    "classid",
                    classid,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        self._run(
            [
                "tc",
                "class",
                "add",
                "dev",
                self.iface,
                "parent",
                self.root_handle,
                "classid",
                classid,
                "htb",
                "rate",
                rate,
                "ceil",
                ceil,
            ]
        )

    def clear_all(self) -> None:
        if self.simulation:
            return
        subprocess.run(
            ["tc", "qdisc", "del", "dev", self.iface, "root"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def list_classes(self) -> str:
        if self.simulation:
            return "(simulation)"
        proc = self._run(["tc", "class", "show", "dev", self.iface])
        return proc.stdout if proc.stdout else proc.stderr


if __name__ == "__main__":
    tc = TcController(iface=os.environ.get("IFACE", "eth0"))
    tc.ensure_root_qdisc()
    print(tc.list_classes())
