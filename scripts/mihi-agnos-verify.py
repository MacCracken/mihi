#!/usr/bin/env python3
# mihi-agnos-verify — prove mihi's own probe surface on the REAL agnos kernel in
# QEMU, with a control arm that fails.
#
# ⭐ WHAT THIS EXISTS TO SETTLE. mihi 1.2.3 (audit finding A-5) gave
# `mihi_mem_free` the AGNOS arm it never had: before it, that probe fell through
# to a Linux `open("/proc/meminfo")` the sovereign kernel cannot satisfy and
# returned `0 - 1` forever. Every previous agnos claim in this repo was made
# through `iam`, which renders a missing figure as blank, so the gap was never
# visible from the outside.
#
# The fix is only worth as much as the control arm beside it, which is what the
# agnos harness README demands ("a passing test that would also pass when broken
# is worthless"):
#
#   /bin/mihismc  — programs/agnos_probe.cyr built from the 1.2.2 source.
#                   MUST print "free B:  -1".
#   /bin/mihism   — the same program built from this working tree.
#                   MUST print a positive "free B:" and reach "probe ok".
#
# ⛔ The vehicle is programs/agnos_probe.cyr, NOT programs/smoke.cyr. smoke
# links src/gpu.cyr and therefore the ai-hwaccel bundle, which is mihi's
# standing agnos blocker; built --agnos it faults before its first println
# (`run: exit 142`, measured here 2026-08-23 for the 1.2.2 binary and this
# tree's alike). agnos_probe includes only the five agnos-clean modules.
#
# Both run in ONE boot, control first, so the pair is taken under identical
# conditions. PASS requires the control to fail in the expected way AND the
# new binary to succeed — a green control means the harness is measuring
# nothing and the run is reported as inconclusive, not as a pass.
#
# Prereqs:
#   agnos/build/agnos            (sh scripts/build.sh in agnos)
#   agnos/build/rootfs/bin/agnsh (sh scripts/burn/stage-tools.sh --build)
#   gnoboot/build/BOOTX64.EFI
#   build/mihi-agnos-probe (cyrius build --agnos programs/agnos_probe.cyr ...)
#   MIHI_AGNOS_PROBE / MIHI_AGNOS_PROBE_CONTROL env vars override the paths.
#
# Modeled on owl/scripts/owl-agnos-verify.py and agnos/scripts/harness/*.
import socket, subprocess, sys, time, os

MIHI  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # .../mihi
REPOS = os.path.dirname(MIHI)                                                # .../Repos
AGNOS_ROOT = os.path.join(REPOS, "agnos")
GNOBOOT = os.environ.get("GNOBOOT_ROOT", os.path.join(REPOS, "gnoboot")) + "/build/BOOTX64.EFI"
AGNOS   = os.path.join(AGNOS_ROOT, "build/agnos")
ROOTFS  = os.path.join(AGNOS_ROOT, "build/rootfs")
PROBE   = os.environ.get("MIHI_AGNOS_PROBE", os.path.join(MIHI, "build/mihi-agnos-probe"))
CTRL    = os.environ.get("MIHI_AGNOS_PROBE_CONTROL", "")
WORK    = os.path.join(MIHI, "build/mihi-agnos-verify")
SEED    = os.path.join(WORK, "seed")
IMG     = os.path.join(WORK, "agnos-mihi.img")
SER     = os.path.join(WORK, "serial-mihi.log")
MON     = "/tmp/agnos-mihi.sock"
PART_OFFSET = 33 * 1048576
PART_BLOCKS = (67 * 1048576) // 4096
FEAT = os.environ.get("EXT2_SMOKE_FEATURES", "^resize_inode,^dir_index,^metadata_csum,^64bit,^uninit_bg")

def p(*a): print(*a, flush=True)

def need(*paths):
    for path in paths:
        if not os.path.exists(path):
            p("FAIL: missing", path); sys.exit(1)
need(GNOBOOT, AGNOS, PROBE, os.path.join(ROOTFS, "bin/agnsh"))
if CTRL and not os.path.exists(CTRL):
    p("FAIL: control binary named but missing:", CTRL); sys.exit(1)

OVMF_CODE = OVMF_VARS = None
for c in ("/usr/share/edk2/x64/OVMF_CODE.4m.fd","/usr/share/edk2/x64/OVMF_CODE.fd",
          "/usr/share/OVMF/OVMF_CODE.fd","/usr/share/OVMF/OVMF_CODE_4M.fd"):
    if os.path.exists(c): OVMF_CODE = c; break
for c in ("/usr/share/edk2/x64/OVMF_VARS.4m.fd","/usr/share/edk2/x64/OVMF_VARS.fd",
          "/usr/share/OVMF/OVMF_VARS.fd","/usr/share/OVMF/OVMF_VARS_4M.fd"):
    if os.path.exists(c): OVMF_VARS = c; break
if not OVMF_CODE or not OVMF_VARS: p("FAIL: OVMF not found"); sys.exit(1)

def sh(cmd):
    r = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if r.returncode != 0:
        p("FAIL step:", cmd, "\n", r.stderr.decode("latin1")[:400]); sys.exit(1)

subprocess.run(["rm","-rf",WORK]); os.makedirs(WORK, exist_ok=True)

# --- seed rootfs: the staged agnos tools + mihi's probe binaries ---
subprocess.run(["cp","-a",ROOTFS,SEED])
subprocess.run(["cp",PROBE,os.path.join(SEED,"bin/mihism")])
os.chmod(os.path.join(SEED,"bin/mihism"), 0o755)
if CTRL:
    subprocess.run(["cp",CTRL,os.path.join(SEED,"bin/mihismc")])
    os.chmod(os.path.join(SEED,"bin/mihismc"), 0o755)

# --- GPT + ESP(gnoboot+kernel) + ext2 rootfs ---
sh(f"dd if=/dev/zero of={IMG} bs=1M count=128 status=none")
sh(f"parted -s {IMG} mklabel gpt mkpart ESP fat32 1MiB 33MiB set 1 esp on mkpart agnos-fs ext2 33MiB 100MiB")
sh(f"sgdisk -t 2:8300 {IMG} >/dev/null")
sh(f"mformat -i {IMG}@@1048576 -F"); sh(f"mmd -i {IMG}@@1048576 ::EFI ::EFI/BOOT ::boot")
sh(f"mcopy -i {IMG}@@1048576 {GNOBOOT} ::EFI/BOOT/BOOTX64.EFI")
sh(f"mcopy -i {IMG}@@1048576 {AGNOS} ::boot/agnos")
sh(f"mkfs.ext2 -F -q -L AGNOS-MIHI -b 4096 -m 0 -O {FEAT} -d {SEED} -E offset={PART_OFFSET} {IMG} {PART_BLOCKS}")
subprocess.run(["cp",OVMF_VARS,os.path.join(WORK,"vars.fd")])
subprocess.run(["chmod","+w",os.path.join(WORK,"vars.fd")])
open(SER,"w").close()
try: os.unlink(MON)
except FileNotFoundError: pass
p("built mihi-agnos-verify image:", IMG)

qemu = subprocess.Popen([
    "qemu-system-x86_64","-machine","q35","-m","512M","-enable-kvm","-cpu","host",
    "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
    "-drive", f"if=pflash,format=raw,file={WORK}/vars.fd",
    "-drive", f"file={IMG},format=raw,if=none,id=disk0",
    "-device","nvme,drive=disk0,serial=AGNOS-MIHI",
    "-device","qemu-xhci,id=xhci","-device","usb-kbd,bus=xhci.0",
    "-serial", f"file:{SER}","-display","none","-no-reboot",
    "-monitor", f"unix:{MON},server,nowait",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

rc = 1
try:
    s = None
    for _ in range(60):
        try: s = socket.socket(socket.AF_UNIX); s.connect(MON); break
        except OSError: time.sleep(0.2)
    if s is None: p("FAIL: no monitor"); sys.exit(1)
    s.settimeout(1.0)

    def drain():
        try:
            while True: s.recv(65536)
        except OSError: pass
    def ser():
        try: return open(SER,"rb").read().decode("latin1")
        except OSError: return ""

    km = {' ':'spc','\n':'ret','-':'minus','.':'dot','/':'slash','_':'shift-minus'}
    def key_for(ch):
        if ch in km: return km[ch]
        if ch.isupper(): return "shift-"+ch.lower()
        return ch

    ok = False
    for _ in range(480):
        if "agnoshi" in ser(): ok = True; break
        time.sleep(0.25)
    p("agnsh banner seen:", ok)
    if not ok: p("FAIL: no agnsh banner"); sys.exit(1)

    # The FIRST keystroke of a session is swallowed by the HID endpoint-registry
    # dispatch (agnos/scripts/harness/README.md). Absorb it with a bare Enter
    # before anything that carries meaning.
    def run_cmd(cmd, want, timeout=90):
        """Type `cmd` at agnsh, retrying the whole line if a key drops, then
        return the serial segment produced after committing it."""
        for _attempt in range(6):
            s.sendall(b"sendkey ret\n"); time.sleep(0.7); drain()
            base = len(ser())
            for ch in cmd:
                s.sendall(("sendkey "+key_for(ch)+"\n").encode()); time.sleep(0.12); drain()
            time.sleep(0.6)
            echoed = ser()[base:].split("[ASSIST] >")[-1]
            if want in echoed:
                m = len(ser())
                s.sendall(b"sendkey ret\n"); time.sleep(1.0)
                deadline = time.time() + timeout
                seg = ""
                while time.time() < deadline:
                    seg = ser()[m:]
                    if "probe ok" in seg or "probe: " in seg or "distro:" in seg: break
                    time.sleep(0.5)
                return seg
            for _ in range(40):
                s.sendall(b"sendkey backspace\n"); time.sleep(0.04)
            drain()
        return None

    ctrl_seg = None
    if CTRL:
        ctrl_seg = run_cmd("run /bin/mihismc", "mihismc")
        p("======== CONTROL (1.2.2 source) on agnos ========")
        p(ctrl_seg if ctrl_seg and ctrl_seg.strip() else "(empty / wedged)")
        p("=================================================")

    seg = run_cmd("run /bin/mihism", "mihism")
    if seg is None:
        p("FAIL: could not type the mihi command cleanly over sendkey (6 tries)")
        s.sendall(b"quit\n"); sys.exit(1)
    p("======== mihi smoke (this tree) on agnos ========")
    p(seg if seg.strip() else "(empty / wedged)")
    p("=================================================")

    # --- assertions ---
    def field(text, label):
        """Return the integer printed after `label`, or None."""
        for line in (text or "").replace("\r", "\n").split("\n"):
            if label in line:
                tail = line.split(label, 1)[1].strip()
                digits = ""
                for ch in tail:
                    if ch == "-" and not digits: digits += ch
                    elif ch.isdigit(): digits += ch
                    else: break
                if digits not in ("", "-"):
                    return int(digits)
        return None

    control_failed_as_expected = True
    if CTRL:
        cfree = field(ctrl_seg, "free B:")
        control_failed_as_expected = (cfree is not None and cfree < 0)
        p("control 'free B:' =", cfree, "(pre-1.2.3 A-5: expected -1)")
        p("control reproduced the pre-1.2.3 A-5 failure:", control_failed_as_expected)

    total_b = field(seg, "total B:")
    free_b = field(seg, "free B:")
    uptime_s = field(seg, "uptime:")
    ncpu = field(seg, "cpus:")
    reached_ok = "probe ok" in seg
    kernel_line = "kernel:" in seg and "AGNOS" in seg
    distro_line = "distro:" in seg and "AGNOS" in seg

    free_ok = free_b is not None and free_b > 0
    total_ok = total_b is not None and total_b > 0
    sane = free_ok and total_ok and free_b <= total_b

    p("kernel identity via uname#34 says AGNOS:", kernel_line)
    p("cpus (sysinfo#35 SI_CPUS) =", ncpu)
    p("total B (sysinfo#35 totalram) =", total_b)
    p("free B  (sysinfo#35 freeram — the A-5 fix) =", free_b)
    p("free <= total (figures are internally consistent):", sane)
    p("uptime s (sysinfo#35 SI_UPTIME) =", uptime_s)
    p("distro reported as AGNOS:", distro_line)
    p("reached 'probe ok':", reached_ok)

    if not control_failed_as_expected:
        p("mihi-agnos-verify: INCONCLUSIVE — the control arm did NOT fail, so this")
        p("  harness is not measuring the A-5 fix. Rebuild the control from the 1.2.2")
        p("  source and re-run; do not read the main arm as a pass.")
        rc = 2
    elif sane and reached_ok and kernel_line and distro_line:
        p("mihi-agnos-verify: PASS — mihi's full probe surface runs on the sovereign")
        p("  kernel. mem_free now answers from sysinfo#35 §4.4 freeram (A-5); the 1.2.2")
        p("  control binary fails at the same call in the same boot.")
        rc = 0
    else:
        p("mihi-agnos-verify: FAIL")
    s.sendall(b"quit\n"); time.sleep(0.2)
finally:
    qemu.terminate()
    try: qemu.wait(timeout=3)
    except subprocess.TimeoutExpired: qemu.kill()
sys.exit(rc)
