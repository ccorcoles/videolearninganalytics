# videolearninganalytics

In order to load a video and record the activity, load jQuery (1.7.2) and Popcorn.js. Then, if the HTML contains a &lt;div id="video"&gt;&lt;/div&gt;, and recorder.php is in the same directory,

			// ensure the web page (DOM) has loaded
			document.addEventListener("DOMContentLoaded", function () {
				
			var t_ini = new Date();
			var t_ara = new Date();
			t_ini.setTime(Date.now());
			var rnd_key = Math.random();
			
			var video = Popcorn.vimeo("#video", "http://vimeo.com/VimeoURL");
			
			video.on("play", function() {
					t_ara.setTime(Date.now());
					$.post("recorder.php", {
					ti: t_ini.toUTCString(),
					rnd: rnd_key,
					vid: "VideoIDToBeRecorded",
					ta: t_ara.toUTCString(),
					acc: "play",
					prms: this.currentTime(),
					});
					}
					);
			
			video.on("seeked", function() {
					t_ara.setTime(Date.now());
					$.post("recorder.php", {
					ti: t_ini.toUTCString(),
					rnd: rnd_key,
					vid: "VideoIDToBeRecorded",
					ta: t_ara.toUTCString(),
					acc: "seek",
					prms: this.currentTime(),
					});
					}
					);
			
			video.on("pause", function() {
					t_ara.setTime(Date.now());
					$.post("recorder.php", {
					ti: t_ini.toUTCString(),
					vid: "VideoIDToBeRecorded",
					rnd: rnd_key,
					ta: t_ara.toUTCString(),
					acc: "pause",
					prms: this.currentTime(),
					});
					}
					);
