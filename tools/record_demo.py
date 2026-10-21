"""Record the isolated screenshot demonstration as an English H.264 MP4."""
from pathlib import Path


def record_demo(window, tickets, source, trip, temporary, output):
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import GLib, Gst
    from PIL import Image, ImageDraw, ImageFont
    from window_capture import capture_x11

    Gst.init(None)
    width, height, fps = 1600, 1120, 15
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    pipeline = Gst.parse_launch(
        f'appsrc name=frames format=time block=true caps=video/x-raw,format=RGB,width={width},height={height},framerate={fps}/1 '
        '! videoconvert ! video/x-raw,format=I420 '
        '! openh264enc bitrate=5000000 complexity=low ! h264parse '
        '! mp4mux faststart=true ! filesink name=destination')
    pipeline.get_by_name('destination').set_property('location', str(output))
    frames = pipeline.get_by_name('frames')
    pipeline.set_state(Gst.State.PLAYING)
    font = ImageFont.truetype('/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf', 28)
    small = ImageFont.truetype('/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf', 18)
    loop = GLib.MainLoop()
    count = 0
    errors = []
    snapshot = temporary / 'video-frame.png'
    title = 'GTasks — Organize your day on GNOME'
    phrase = 'Check the weather forecast'
    def tick():
        nonlocal count, title
        try:
            if count == 4 * fps:
                title = 'Add tasks to keep your plans moving'
            if 4 * fps <= count < 4 * fps + len(phrase) * 2 and count % 2 == 0:
                window._task_panel._entry.set_text(phrase[:(count - 4 * fps) // 2 + 1])
            if count == 8 * fps:
                window._task_panel._entry.emit('activate')
            if count == 11 * fps:
                title = 'Keep notes and dates with each task'
                window._task_action(tickets, 'edit')
            if count == 17 * fps:
                window.get_visible_dialog().close()
                title = 'Break bigger tasks into smaller steps'
            if count == 21 * fps:
                title = 'A layout that adapts to your window'
                window.set_default_size(420, 640)
                window._split_view.set_show_content(True)
            if count == 26 * fps:
                title = 'Local lists offline. Google Tasks when connected.'
                window.set_default_size(900, 640)
                window._split_view.set_show_content(True)
            capture_x11(window.get_surface().get_xid(), snapshot)
            with Image.open(snapshot) as shot:
                shot = shot.convert('RGBA')
                shot.thumbnail((width - 100, height - 170), Image.Resampling.LANCZOS)
                canvas = Image.new('RGB', (width, height), '#eef1f6')
                canvas.paste(shot, ((width-shot.width)//2, 100 + (height-170-shot.height)//2), shot)
            draw = ImageDraw.Draw(canvas)
            draw.text((width//2, 46), title, font=font, fill='#202834', anchor='mm')
            draw.text((width//2, height-30), 'GTasks  •  Demonstration with fictional data', font=small, fill='#566174', anchor='mm')
            buf = Gst.Buffer.new_wrapped(canvas.tobytes())
            buf.pts = buf.dts = count * Gst.SECOND // fps
            buf.duration = Gst.SECOND // fps
            result = frames.emit('push-buffer', buf)
            if result != Gst.FlowReturn.OK:
                raise RuntimeError(f'Video encoder rejected a frame: {result}')
            count += 1
            if count >= 31 * fps:
                loop.quit()
                return GLib.SOURCE_REMOVE
            GLib.timeout_add(1000 // fps, tick)
            return GLib.SOURCE_REMOVE
        except Exception as exc:
            errors.append(exc)
            loop.quit()
            return GLib.SOURCE_REMOVE
    GLib.timeout_add(1000 // fps, tick)
    try:
        loop.run()
        frames.emit('end-of-stream')
        message = pipeline.get_bus().timed_pop_filtered(30 * Gst.SECOND, Gst.MessageType.EOS | Gst.MessageType.ERROR)
        if errors:
            raise errors[0]
        if message is None:
            raise RuntimeError('Video encoder timed out')
        if message.type == Gst.MessageType.ERROR:
            raise RuntimeError(message.parse_error())
    finally:
        pipeline.set_state(Gst.State.NULL)
    print(output, flush=True)
