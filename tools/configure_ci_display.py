"""Provide a real desktop large enough for the original Windows GUI tests.

Only --apply on a Windows GitHub Actions runner may change the display mode.
Running locally without --apply is read-only.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import time


def eligible_modes(modes, width, height):
    return sorted((mode for mode in modes if mode.BitsPerPel >= 32
                   and mode.PelsWidth >= width and mode.PelsHeight >= height),
                  key=lambda mode: (mode.PelsWidth*mode.PelsHeight,
                                    abs(mode.DisplayFrequency-60)))


def configure(api, constants, *, width, height, apply=False):
    def size():
        return [api.GetSystemMetrics(0), api.GetSystemMetrics(1)]
    before = size()
    report = dict(before=before, minimum=[width,height], changed=False)
    if before[0] < width or before[1] < height:
        modes = []
        index = 0
        while True:
            try:
                mode = api.EnumDisplaySettings(None,index)
            except api.error:
                break
            if mode is None:
                break
            modes.append(mode)
            index += 1
        candidates = eligible_modes(modes,width,height)
        report['available_modes'] = sorted({(m.PelsWidth,m.PelsHeight,m.BitsPerPel) for m in modes})
        if not apply:
            report.update(after=before, ready=False)
            return report
        if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('RUNNER_OS') != 'Windows':
            raise RuntimeError('Display changes are restricted to Windows GitHub Actions runners')
        failures = []
        for mode in candidates:
            result = api.ChangeDisplaySettings(mode,constants.CDS_TEST)
            if result == constants.DISP_CHANGE_SUCCESSFUL:
                result = api.ChangeDisplaySettings(mode,0)
                if result == constants.DISP_CHANGE_SUCCESSFUL:
                    report['changed'] = True
                    break
            failures.append([mode.PelsWidth,mode.PelsHeight,result])
        else:
            raise RuntimeError('No usable CI desktop mode: '+json.dumps({**report,'failures':failures}))
        deadline = time.monotonic()+5
        while time.monotonic() < deadline and (size()[0] < width or size()[1] < height):
            time.sleep(.1)
    after = size()
    report.update(after=after,ready=after[0] >= width and after[1] >= height)
    if apply and not report['ready']:
        raise RuntimeError('Desktop remained too small: '+json.dumps(report))
    return report


def main():
    import win32api
    import win32con
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--min-width',type=int,default=1920)
    parser.add_argument('--min-height',type=int,default=1080)
    parser.add_argument('--report',type=Path)
    args = parser.parse_args()
    result = configure(win32api,win32con,width=args.min_width,height=args.min_height,apply=args.apply)
    output = json.dumps(result,indent=2)
    print(output)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(output+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
