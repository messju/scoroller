#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, optparse, re
import pygame

def main(options):

    # init screen
    pygame.init()

    if options.fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        (options.width, options.height) = screen.get_size()
    else:
        screen = pygame.display.set_mode((options.width, options.height))
    
    pygame.display.set_caption("Scores")
    pygame.mouse.set_visible(0)
    pygame.key.set_repeat(1, options.fps)
    
    clock = pygame.time.Clock()
    font = pygame.font.Font(options.basedir + "C64_Pro_Mono_v1.0-STYLE.ttf", options.font_size)
    
    if options.y_pos == None:
        options.y_pos = int((options.height - options.font_size) / 2)
    running = True
    x_pos = options.width

    text = []
    text_pos = 0
    stat = None

    while running:
        clock.tick(options.fps)

        # handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # quit
                running = False
                    
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

        # check if file changed or file was not read before
        old_stat = stat
        stat = os.stat(options.text_file)
        if (not old_stat) or (stat.st_mtime != old_stat.st_mtime) \
           or (stat.st_size != stat.st_size):

            f = open(options.text_file, "r")
            text = re.split("\r?\n", f.read())
            text = [line.strip() for line in text if line.strip() != ''] # remove empty lines
            text_pos = 0
            x_pos = options.width

        # draw scene
        screen.fill((0x00, 0x00, 0x00))

        x = x_pos
        y = options.y_pos
        t = text_pos
        while x < options.width:
            if len(text) > 0:
                chunk = font.render(text[t] + options.separator, 1, options.text_color)
                # print "%d %d %s" % (t, x, text[t])

                screen.blit(chunk, (x, y))
                x += chunk.get_width()
                if x < 0:
                    text_pos = (text_pos + 1) % len(text)
                    x_pos = x
                elif x >= options.width:
                    break

                t = (t + 1) % len(text) 
            else:
                break

        x_pos = x_pos - options.speed

        # show screen
        pygame.display.flip()
        
if __name__ == '__main__':
    options_error = False
    parser = optparse.OptionParser()
    parser.add_option("-f", "--full-screen", action="store_true",
                      dest="fullscreen", help="toogle fullscreen mode")
    parser.add_option("-g", "--geometry", type="string", default="320x240", action="store",
                      dest="geometry", help="screen size in [width]x[height]")
    parser.add_option("-y", "--y-pos", type="int", default=None, action="store",
                      dest="y_pos", help="y position")
    parser.add_option("--fps", type="int", default=100, action="store",
                      dest="fps", help="frames per second")
    parser.add_option("-s", "--speed", type="int", default=1, action="store",
                      dest="speed", help="scroll speed in pixels per frame")
    parser.add_option("--font-size", type="int", default=36, action="store",
                      dest="font_size", help="font size")
    parser.add_option("-t", "--text-file", type="string", default="scoroller.txt", action="store",
                      dest="text_file", help="text filename")
    (options, args) = parser.parse_args()

    options.separator = u' ••• '
    options.text_color = (0xff, 0xff, 0xff)

    match = re.search("^(\d+)x(\d+)$", options.geometry) # split geometry string
    if match:
        options.width = int(match.group(1))
        options.height = int(match.group(2))
    else:
        options_error = True

    options.basedir = os.path.dirname(os.path.abspath(__file__)) + "/"
    options.images = args

    if options_error:
        parser.print_usage()
    else:
        main(options)

