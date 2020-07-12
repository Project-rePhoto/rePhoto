navigator.mediaDevices.getUserMedia({
	video: true
})
.then(function(stream){
	//Stream stuff
	vid.onloadedmetadata = function() {
		this.width = overlay.width = this.videoWidth;
		this.height = overlay.height = this.videoHeight;
	}
	vid.srcObject = stream;
	vid.play();
	overlay.onclick = function() {
		var c = document.createElement('canvas');
		c.width = vid.videoWidth;
		c.height = vid.videoHeight;
		c.getContext('2d').drawImage(vid, 0, 0);
		c.toBlob(capturedImage);
	};
})
.catch(function(err){
	// Handle the error
	console.error(err);
});

function capturedImage(blob){
	// creates DOMString containing a URL representing the object
	var url = URL.createObjectURL(blob);
	
	//Acquire new HTML image instance
	var img = new Image();

	//onload image, clear object url and set img src
	img.onload = function() {
		URL.revokeObjectURL(url);
	};
	img.src = url;

	// Remove vid object and replace overlay with img
	URL.revokeObjectURL(vid.src);
	overlay.parentNode.appendChild(img);
	vid.parentNode.removeChild(vid);
	overlay.parentNode.removeChild(overlay);
}