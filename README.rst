Log helper
=====

Log helper a simple media sync tool. Adds timecode to video by calculating it from audio

When the timecode of the camera and the audio recorder are not synchronized, you can synchronize the clips by shifting the timecode of the video clips by the difference in timecodes.

Works with xml fcp7 (xmeml version="5")

Installing
----------

Install and update using `pip`_:

.. code-block:: text

    $ pip install -U log_helper

.. _pip: https://pip.pypa.io/en/stable/getting-started/



Usage
-----

log_helper [-h] [-b] [-n|p] [-nr] [-m] [-B] [--testing] file

positional arguments:
  file

optional arguments:
  -h, --help      show this help message and exit
  -b, --bin      create bins
  -n, --next_day      in name clip using next date
  -p, --prev_day      in name clip using previous date
  -nr, --rename      rename video clips by audio (if the parameter is specified, then renaming does not occur)
  -B, --batch      process each bean separately
  --testing      shows info for each clip


In the sequence of clips on the first clip (both video and audio), put IN on the clapper, on the last OUT

If not set IN OUT an exception is thrown errors.DeltaBaseZero
