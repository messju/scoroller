#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, optparse, re
import pygame
import random

def main(options):

    # init screen
    pygame.init()

    opts = 0
    if options.fullscreen:
        opts |= pygame.FULLSCREEN

    if options.hwsurface:
        opts |= pygame.DOUBLEBUF | pygame.HWSURFACE

    if options.fullscreen:
        screen = pygame.display.set_mode((0, 0), opts)
        options.screen_resolution =(screen.get_width(), screen.get_height())
    else:
        screen = pygame.display.set_mode(options.screen_resolution, opts)
        screen.fill(options.debug_color)
        screen.set_clip((0, 0), (options.width, options.height))

    pygame.display.set_caption("OCM Scores")
    pygame.mouse.set_visible(0)
    pygame.key.set_repeat(1, options.fps)

    clock = pygame.time.Clock()
    font_filename = options.basedir + "C64_Pro_Mono_v1.0-STYLE.ttf"
    font1 = pygame.font.Font(font_filename, options.font_size)
    font2 = pygame.font.Font(font_filename, int(round(options.font_size * options.font_size_factor)))

    running = True

    # for each score set (pair of two lines) we show one scene of screen_width*2 frames
    # each scene is separated in 4 quarters (one quarter = screen_width/2 frames)
    # line 1 behaves identically in all 4 quarters (it's a simple scroller)
    # line 2 behaves differently in each quarter
    #    1st quarter: build up line two frome the center of screen
    #    2nd quarter: do nothing, just show line 2 centered
    #    3rd and 4th quarter: scroll away line2 using an accelerated scrolling

    text = []
    stat = None
    frame = 0

    # main loop
    while running:
        # handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # quit
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

        if frame == 0:
            # setup

            # check if file changed or file was not read before
            old_stat = stat
            stat = os.stat(options.text_file)
            if (not old_stat) or (stat.st_mtime != old_stat.st_mtime) \
               or (stat.st_size != stat.st_size):

                f = open(options.text_file, "r")
                text = re.split("\r?\n", f.read()) # split lines (handles windows \r if necessary)
                text = [line.strip() for line in text if line.strip() != ''] # remove empty lines

            # we have one surface with all scores' texts: the "scroll"

            # get height of list of all scores (the "scroll")
            scroll_height = 0
            for text_pos in range(0, len(text) - 1, 2):
                # line1 is the game title (odd line numbers in the text file)
                text1 = font1.render(text[text_pos], 1, options.text_color)
                scroll_height += text1.get_height() + 3

                # line2 is the game score and the champions name (even line numbers in the text file)
                text2 = font2.render(text[text_pos + 1], 1, options.text_color)
                scroll_height += text2.get_height() + 3 + 30
                scroll_height += 30

            scroll = pygame.Surface((options.width, scroll_height))
            scroll.fill(options.bg_color)

            scroll_y = 0
            for text_pos in range(0, len(text) - 1, 2):
                # line1 is the game title (odd line numbers in the text file)
                text1 = font1.render(text[text_pos], 1, options.text_color)
                scroll.blit(text1, ((options.width - text1.get_width() ) // 2, scroll_y))
                scroll_y += text1.get_height() + 3

                # line2 is the game score and the champions name (even line numbers in the text file)
                text2 = font2.render(text[text_pos + 1], 1, options.text_color)
                scroll.blit(text2, ((options.width - text2.get_width() ) // 2, scroll_y))
                scroll_y += text2.get_height() + 3
                scroll_y += 30

            if options.debug_start_frame != None:
                frame = options.debug_start_frame

            frames_max = scroll_height + 400

        # draw scene
        screen.fill(options.bg_color)

        w = 200
        y = options.y_pos
        a = 0.4
        for scan_row in range(0, 400):
            row = (frame - 400 + scan_row)

            if row >= 0 and row < scroll.get_height():
                scanline = pygame.Surface((scroll.get_width(), 1))
                scanline.blit(scroll, (0, 0), area=((0, row), (scroll.get_width(), 1)))
                # scanline.fill(options.text_color)
                scanline = pygame.transform.scale(scanline, (w, 1))

                x = (screen.get_width() - scanline.get_width()) // 2
                screen.blit(scanline, (x, y))

            y += a
            a = a + 0.001
            w += 2

        # show screen and tryp to keep at the target FPS
        pygame.display.flip()
        
        if options.use_busy_loop:
            clock.tick_busy_loop(options.fps)
        else:
            clock.tick(options.fps)

        if options.show_fps and quarter_step % (options.fps // 3) == 0:
            print("%8.4f\r" % clock.get_fps()),
            sys.stdout.flush()
            
        # go to next frame
        frame += options.speed

        if (options.debug_end_frame != None) and (frame >= options.debug_end_frame):
            frame = frames_max

        if frame >= frames_max:
            frame = 0

        # end of main loop

    # end of main

if __name__ == '__main__':
    options_error = False
    parser = optparse.OptionParser()
    parser.add_option("-f", "--full-screen", default=False, action="store_true",
                      dest="fullscreen", help="toogle fullscreen mode")

    parser.add_option("--hw-surface", action="store_true",
                      dest="hwsurface", help="use hardware acceleration for pygame surfaces")

    parser.add_option("--use-busy-loop", default=False, action="store",
                      dest="use_busy_loop", help="report actual fps to stdout")

    parser.add_option("--geometry", type="string", default="800x600", action="store",
                      dest="geometry", help="screen size in [width]x[height]")

    parser.add_option("--y-pos", type="int", default=360, action="store",
                      dest="y_pos", help="y position of row 1")

    parser.add_option("--fps", type="int", default=30, action="store",
                      dest="fps", help="frames per second")

    parser.add_option("--show-fps", default=False, action="store",
                      dest="show_fps", help="report actual fps to stdout")

    parser.add_option("--speed", type="int", default=3, action="store",
                      dest="speed", help="scroll speed in pixels per frame")

    parser.add_option("--font-size", type="int", default=44, action="store",
                      dest="font_size", help="font size")

    parser.add_option("--font-size-factor", type="float", default=0.7, action="store",
                      dest="font_size_factor", help="ratio between font sizes of row 1 and 2")

    parser.add_option("--text-file", type="string", default="ocm-scores.txt", action="store",
                      dest="text_file", help="text filename")

    parser.add_option("--debug-start-frame", type="int", default=None, action="store",
                      dest="debug_start_frame", help="debig start frame")

    parser.add_option("--debug-end-frame", type="int", default=None, action="store",
                      dest="debug_end_frame", help="debig end frame")

    (options, args) = parser.parse_args()

    options.text_color = (0xff, 0xff, 0xff)
    options.bg_color = (0x00, 0x00, 0x00)
    options.debug_color = (0xc0, 0x00, 0x00)

    options.screen_resolution = (800, 600)
    match = re.search("^(\d+)x(\d+)$", options.geometry) # split geometry string
    if match:
        options.width = int(match.group(1))
        options.height = int(match.group(2))
    else:
        options_error = True

    options.basedir = os.path.dirname(os.path.abspath(__file__)) + "/"

    if options_error:
        parser.print_usage()
    else:
        main(options)

