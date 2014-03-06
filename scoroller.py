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

    screen = pygame.display.set_mode((options.width, options.height), opts)

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
    text_pos = 0
    stat = None

    frame = 0
    frames_max = options.width * 2 # scene duration

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

                if options.text_start_random:
                    text_pos = random.randint(0, len(text) - 1)
                    text_pos = text_pos - text_pos % 2
                else:
                    text_pos = 0

            # we have one surface per text line (line1 and line2).
            # each surface has the full screen width, the full text's
            # height. the text is placed centered on that surface.
            
            # line1 is the game title (odd line numbers in the text file)
            text1 = font1.render(text[text_pos], 1, options.text_color)
            line1 = pygame.Surface((options.width, text1.get_height()))
            line1.fill(options.bg_color)
            line1.blit(text1, ((options.width - text1.get_width() ) // 2, 0))

            # line2 is the game score and the champions name (even line numbers in the text file)
            text2 = font2.render(text[text_pos + 1], 1, options.text_color)
            line2 = pygame.Surface((options.width, text2.get_height()))
            line2.fill(options.bg_color)
            line2.blit(text2, ((options.width - text2.get_width() ) // 2, 0))

            # temp surfaces used in 1st quarter
            temp1 = pygame.Surface((options.width // 2, text2.get_height()))
            temp1.fill(options.bg_color)
            temp2 = pygame.Surface((options.width // 2, text2.get_height()))
            temp2.fill(options.bg_color)

            # skip a few frames in the beginning if neither of the two lines is very wide
            #   this avoids too long pauses between two scenes
            frame = (options.width - max(text1.get_width(), text2.get_width())) // 2

            # accelerated scroller params for 2nd half of the scene
            x_pos2 = 0
            x_speed = 10.5
            x_accel = -0.35

            # flip scrolling direction in 2nd half:
            #    1st score line leaves to the left, 2nd leaves to right, 3rd to the left...
            if text_pos // 2 % 2 == 1:
                x_speed = -x_speed
                x_accel = -x_accel

            if options.debug_start_frame != None:
                frame = options.debug_start_frame

        # draw scene

        quarter = frame * 4 // frames_max         # ranging from 0..3
        quarter_step = frame % (frames_max // 4)  # ranging i.e. 0..319 in each quarter

        screen.fill(options.bg_color)

        # that is all to handle the game title scrolling
        screen.blit(line1, (options.width - frame, options.y_pos1))

        if quarter == 0: # build up line 2 from the center
            x = options.width // 2 - quarter_step
            temp1.blit(line2, (x, 0))
            screen.blit(temp1, (0, options.y_pos2))

            x = - options.width + quarter_step
            temp2.blit(line2, (x, 0))
            screen.blit(temp2, (options.width // 2, options.y_pos2))

        elif quarter == 1: # just show line 2
            screen.blit(line2, (0, options.y_pos2))

        else: # quarter == 2 or quarter == 3: # scroll away line 2
            if abs(x_pos2) < options.width:
                screen.blit(line2, (int(x_pos2), options.y_pos2))
            x_pos2 += x_speed
            x_speed += x_accel

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
            text_pos = (text_pos + 2) % len(text) # get next pair of text lines
            

        # end of main loop

    # end of main

if __name__ == '__main__':
    options_error = False
    parser = optparse.OptionParser()
    parser.add_option("-f", "--full-screen", action="store_true",
                      dest="fullscreen", help="toogle fullscreen mode")

    parser.add_option("--hw-surface", action="store_true",
                      dest="hwsurface", help="use hardware acceleration for pygame surfaces")

    parser.add_option("--use-busy-loop", default=False, action="store",
                      dest="use_busy_loop", help="report actual fps to stdout")

    parser.add_option("--geometry", type="string", default="640x480", action="store",
                      dest="geometry", help="screen size in [width]x[height]")

    parser.add_option("--y-pos1", type="int", default=360, action="store",
                      dest="y_pos1", help="y position of row 1")

    parser.add_option("--y-pos2", type="int", default=440, action="store",
                      dest="y_pos2", help="y position of row 2")

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

    parser.add_option("--text-file", type="string", default="scoroller.txt", action="store",
                      dest="text_file", help="text filename")

    parser.add_option("--text-start-random", default=True, action="store",
                      dest="text_start_random", help="start scrolling by first line or by a random line")

    parser.add_option("--debug-start-frame", type="int", default=None, action="store",
                      dest="debug_start_frame", help="debig start frame")

    parser.add_option("--debug-end-frame", type="int", default=None, action="store",
                      dest="debug_end_frame", help="debig end frame")

    (options, args) = parser.parse_args()

    options.text_color = (0xff, 0xff, 0xff)
    options.bg_color = (0x00, 0x00, 0x00)

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

