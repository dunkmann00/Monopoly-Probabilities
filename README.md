# Monopoly-Probabilities
Simulate a Monopoly game to generate the probabilities of landing on each
square.

While this project was originally inspired by the YouTube video
[The Mathematics of Winning Monopoly](https://youtu.be/ubQXz5RBBtU) by Stand-up
Maths, it kind of grew into a way for me to play around with how to best share a
python project. I wanted to make it easy for someone who was not a developer/not
familiar with the command line, to be able to run this. Over time, this led me
down a rabbit hole that has culminated in the current version of this
repository. I'd love to continue to expand on this and add other ways to package
up a Python project. Each approach has its pros and cons, so it is interesting
(and useful) to try them out.

## Getting Started

If you just want to run the simulation, you can download the prebuilt binaries
from the latest
[release](https://github.com/dunkmann00/Monopoly-Probabilities/releases). Make
sure to download the correct version for your OS! Once downloaded, run the
executable and it will perform the simulation and output the results in a
directory called `results`, located in the current working directory. For more
details on running the prebuilt binaries, see
[Running the Binaries](#running-the-binaries).

If you would like to run Monopoly-Probabilities as a regular Python package or
build a binary yourself then keep reading...

## Running or Building from source

This project was built around the idea that it should be simple for anyone to
run it. Initially this meant setting up a simple environment, but has since
evolved into providing prebuilt binaries you can just download and run. You
can't get much simpler than a prebuilt binary (well...if it works on your
machine anyway) but as I added the ability to make the binaries, I kept on with
the idea of making it simple for anyone to do. The project comes with the
`scriptopoly` command, which has the capability to do everything from setting up
the virtual environment to building the binaries. Its as easy as running a
simple cli command. Now anyone should be able to build the binaries on their own
machine (Windows, macOS, or Linux) since all the details are taken care of for
you.

### Important

1. **The following assumes you cloned the repository onto your own machine. For
   help doing that see GitHub's
   ["Cloning a Repository"](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository).**

1. **Make sure to run the commands below with Monopoly-Probabilities as your
   current working directory.**

## Setting up the Environment

When working with a Python project the first thing you should generally do is
setup a virtual environment. To do that and install the Monopoly-Probabilities
project into it run:
```
python install_monopoly.py
```
*If python is a different command on your machine (like `python3`) run that
instead.*

Once you've done that activate the virtual environment:

Mac/Linux:
```
. venv/bin/activate
```

Windows:
```
venv\Scripts\activate.bat
```

## Running the Simulation

Now that we have setup and activated our virtual environment, we have access to
the `monopoly` command. Run the command to run the simulation:
```
monopoly
```

If everything is working, you should see the output telling you the number of
cores, turns (moves), and time it took to complete. There will also be a `csv`
and `txt` file in the `results` directory with the data from the simulation.

Running the `monopoly` command by itself runs with 100 turns by default. To run
the simulation with a different number of turns you can use the `--turns`
argument:
```
monopoly --turns 1000000
```

That would run the simulation with 1,000,000 turns! There is no limit to the
number of turns you can run, it just might take a while. But surely there must
be some way to make it go faster? Why yes, there is!

## Building the C extension of the Monopoly Class

Inside the project there is the `Monopoly` class. This encapsulates the logic of
how a game of Monopoly works. Not the whole thing, just how taking turns,
rolling the dice, and moving around the board works. Just the things we need to
run the simulation. When we ran the simulation before, it ran with the *'Pure
Python'* version of the Monopoly class. Running with 1,000,000 turns might have
seemed pretty fast, probably taking just a few seconds to complete. But, thats
not nearly as fast as we could get it to run if we use the C extension version
that Monopoly-Probabilities can build for us with the help of the `scriptopoly`
command.

To build the C extension run:
```
scriptopoly build
```

After that is finished run the simulation again:
```
monopoly --turns 1000000
```

What did I tell you? Was that not blazing fast!

## Other Configuration Options

If you run `monopoly --help` you can see other options that can be passed in to
configure how the simulation will run.

## Building the Binaries

When sharing a python application with someone who does not have python
installed on their machine, there are at least 2 things you can do.

1. Have them install python.
1. Freeze (aka bundle or package) the application into a single standalone
   package. In this case just a binary file.

The first option is certainly more complicated for them, but simpler for you.
While the second option is much simpler for them, but more complicated for you.
It was also something I wanted to look into anyway so I added the ability to
package Monopoly-Probabilities into a standalone binary. There are multiple
tools that exist to do this, so I figured I would provide the ability to
build the binary with a few that I thought seemed like they were worth trying.

You can build Monopoly-Probabilities with the following tools:

| Name | Homepage | Repository |
|------|----------|------------|
| PyInstaller | https://pyinstaller.org/en/stable/ | https://github.com/pyinstaller/pyinstaller |
| PyOxidizer | https://pyoxidizer.readthedocs.io/en/stable/pyoxidizer.html | https://github.com/indygreg/PyOxidizer |
| Nuitka | https://nuitka.net/ | https://github.com/Nuitka/Nuitka |

For a look at my thoughts on working with these tools see
[Experience with Build Tools](#experience-with-build-tools).

Before we can build a binary with any of the previously mentioned tools, we need
to install them into our virtual environment:
```
scriptopoly install
```

This installs all of the tools and their dependencies and does so with pinned
versions. Pinning the versions ensures that even if a newer version of one of
the tools is released, it won't silently get installed without us knowing. This
can help avoid future build errors.

Now that we have that taken care of, let's build the binary using PyInstaller.
Run:
```
scriptopoly pyinstaller
```

Et-Voilà! If it worked you should have seen a bunch of output to the screen
followed by 'Done'. Inside the `dist` directory there should be a `pyinstaller`
directory and inside that a file called `monopoly` (or `monopoly.exe` on
Windows). This is the entire Monopoly-Probabilities project, including the
python interpreter, all nice and neatly packaged into a single file. Pretty
cool!

The other tools can also be run in the same way. There's even the convenience
command `all-binaries`, which will build a binary with each tool. There are a
few arguments that can be specified to the build commands to build the binary in
a 'non-standard' way. These can be viewed by passing `--help` after each
command.

## Running the Binaries

To run the simulation with the binary we built (or downloaded) with PyInstaller
we run:

Mac/Linux:
```
dist/pyinstaller/monopoly
```

Windows:
```
dist\pyinstaller\monopoly.exe
```

If everything worked the output should be the same as it was before when we ran
the simulation with regular python. These binaries also take the same arguments
as they did before (as a refresher, run `monopoly --help` to see all the
arguments available).

## Experience with Build Tools

I'll list a few notes reviewing my experiences with these tools:
- I found all of these tools to work well for building Monopoly-Probabilities.
- PyOxidizer was a little more complicated to get the build configuration setup.
- They all required slight changes to the original project to handle
  multiprocessing.
- Nuitka is still giving me difficulties with multiprocessing. At the moment,
  running Nuitka in multi-core mode is disabled. To force the Nuitka binary to
  run in multi-core mode, set the `FORCE_NUITKA_MULTI` environment variable.
