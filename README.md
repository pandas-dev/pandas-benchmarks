# pandas benchmark

## Set up instructions

Install the compilers needed to build pandas in the system:

```shell
apt install gcc g++
```

Create a user to run the benchmarks, and clone this repository in its home.

Install [pixi](https://prefix.dev), which we use to manage the environment that runs
asv. Note that the the environment to run the benchmarks is managed by asv and it is
different from the pixi environment:

```shell
curl -fsSL https://pixi.sh/install.sh | bash
```

Clone the pandas repository inside the `pandas-benchmarks` directory:

```shell
cd pandas-benchmarks
git clone https://github.com/pandas-dev/pandas.git
```

## Run benchmarks

We use [pixi](https://prefix.dev) to manage the environment and run the benchmarks:

```shell
pixi run bench
```

We may want to implement a script that runs benchmarks continually (a new run starts
when the previous finishes, indefinetly). But for now we are using cron.

To set up cron to run the benchmarks automatically we can use:

```
0 */3 * * * cd pandas-benchmarks && /home/bench/.pixi/bin/pixi run bench >> bench.log 2>&1
```

Note that the frequency should avoid starting a new job when the previous
has not finished, so if the benchmarks take 2.5 hours to complete, we should
schedule the runs to for example every 3 hours.

To view the log of cron executions we can run:

```shell
grep CRON /var/log/syslog | grep "(bench)"
```

## System stability

Everything that happens in the system while running the benchmarks causes an
impact, meaning that benchmarks will run faster when there is not much noise,
and will run slower when there is. For example, if the core running the benchmarks
takes care of an operating system interruption, this will cause a context switch,
will flush the CPU caches, and the benchmark will take longer. Even if every
benchmark is run multiple times, this variance makes our results worse and likely
to cause false positives. This section is about trying to make the system more
stable and reduce the variance of the execution time of benchmarks.

### CPU isolation

First thing we can do is to isolate the CPUs where the benchmarks run. This means
that the operating system won't use the CPU unless a process is explicitly started
with a CPU affinity to that core.

First, to check the cores available in the system we can run:

```shell
$ lscpu --all --extended
CPU NODE SOCKET CORE L1d:L1i:L2:L3 ONLINE    MAXMHZ   MINMHZ       MHZ
  0    0      0    0 0:0:0:0          yes 4900.0000 800.0000 4798.3130
  1    0      0    1 1:1:1:0          yes 4900.0000 800.0000 4603.2891
  2    0      0    2 2:2:2:0          yes 4900.0000 800.0000 4000.0000
  3    0      0    3 3:3:3:0          yes 4900.0000 800.0000 4000.0000
  4    0      0    0 0:0:0:0          yes 4900.0000 800.0000 4000.0000
  5    0      0    1 1:1:1:0          yes 4900.0000 800.0000 4000.0000
  6    0      0    2 2:2:2:0          yes 4900.0000 800.0000 4782.7388
  7    0      0    3 3:3:3:0          yes 4900.0000 800.0000 4000.0000
```

The `CPU` column shows that the benchmarks server has 8 cores, and the `CORE`
column shows that those are using 4 different physical cores (every physical
core is used by two separate pipelines or virtual cores, referred by Intel
as hyperthreads). We need to isolate physical cores, so the OS does not
execute anything in the other pipeline either, which would also slow down
the benchmark execution.

To isolate CPUs we need to add parameters to the kernel. To do so, we edit
the file `/etc/default/grub` and do these changes:

```
# Find this line:
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"

# Replace it with this line (add the parameters at the end):
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash isolcpus=3,7 nohz_full=3,7"
```

This will isolate the physical core 3, via its two virtual cores 3 and 7.
It will also remove these cores from the operating system scheduler ticks.
We can surely isolate more cores, for now we just start by one for simplicity.

For the changes to have an effect we first need to update the actual grub
configuration with the changes in `/etc/default/grub.d/50-cloudimg-settings.cfg`.
In general `/etc/default/grub` is used for grub settings, but OVH overwrites the
content of that file with `50-cloudimg-settings.cfg`. Note that grub does not read
directly from those files, so it is needed to execute `update-grub` or `grub-mkconfig`
which parse these files and write to `/boot/grub.grub.cfg` which is the one used by
the operating system. After executing one of those commands it is needed to restart
the system so the running kernel contains the new parameters. In practice this is as
simple as tuning the next commands

```shell
$ sudo vim /etc/default/grub.d/50-cloudimg-settings.cfg  # and make changes above
$ sudo update-grub
$ sudo reboot
```

Once the system is restarted we should check that the CPUs are indeed
isolated as expected. This can be done checking the information in the
next files:

```shell
$ cat /sys/devices/system/cpu/isolated
3,7
```

We can also see that the operating system is not running tasks in the isolated CPUs
by generating process and checking CPU usage with htop:

```shell
$ apt install stress
$ stress --cpu 8
$ htop # in a different terminal
```

Isolation works for processes running in the user space, but not in the system space.
Ideally, we would like to avoid interruptions running in our isolated kernel. While
this is a complex topic, and not all intererruptions can run in any core, to limit the
number of cores every interruption runs in a general way, this command can be used:

```shell
for IRQ_AFFINITY_FILE in $(find . -name smp_affinity); do echo 77 | sudo tee $IRQ_AFFINITY_FILE; done
```

Note that for some interruptions the command will fail. Also note that `77` is a binary
mask in hexadecimal representing `0111 0111` (4th and 8th CPUs are not allowed to run the
interruption).

## CPU frequency

Modern CPUs are able to scale their frequency depending on work load or temperature. When a CPU
is idle it will decrease its frequency to save energy. Also, when a CPU is busy and its temperature
increases, it will eventually decrease its frequency so the temperature goes back to safe level.

Most of these frequency scaling technologies can be disabled via the system BIOS, but we do not
have control of it in the servers in a data center, and disabling them may make frequency slow, and
the benchmark suite take much longer to run (something like double the time based on past tests).

There are some things we have control of at runtime. We should be able to disable TurboBoost via:
```shell
echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
```

We can also install `cpufreq` which gives informations and allow to control certain features with:

```shell
sudo apt install linux-tools-generic
```

## Benchmarks variance

While the system introduces noise to due to CPU scaling or our benchmark process being interrupted
by other processes and interruptions, there are other sources of noise that cause variance in the
results of our benchmarks.

The main ones identifies are:
- I/O operations
- Unpredictable CPU cache misses
- Randomness (for example, our benchmarks on functions that check duplicates are affected by the
  randomness in the hashing functions for the used hash tables).
