<head>
    <style>
html, body {
    font-family: arial;
    padding: 0 2em;
    font-size: 18px;
    background: #111;
    color: #aaa;
    text-align:center;
}

h1 {
    font-size: 3em;
    font-weight: 100;
}

p {
    font-weight: 100;
    color: #888;
    margin-bottom: 45px;
}

.footer { 
    font-style: italic;
    margin-top: 80px;
}

a {
    text-decoration: none;
}


/* ------------------------------------------------------------------------------*/
.thumb {
    max-height: 171px;
    border: solid 6px rgba(5, 5, 5, 0.8);
}

.lightbox {
    position: fixed;
    z-index: 999;
    height: 0;
    width: 0;
    text-align: center;
    top: 0;
    left: 0;
    background: rgba(0, 0, 0, 0.8);
    opacity: 0;
}

.lightbox img {
    max-width: 90%;
    max-height: 80%;
    margin-top: 2%;
    opacity: 0;
}

.lightbox:target {
    /** Remove default browser outline */
    outline: none;

    width: 100%;
    height: 100%;
    opacity: 1 !important;
    
}

.lightbox:target img {
    border: solid 17px rgba(77, 77, 77, 0.8);
    opacity: 1;
    webkit-transition: opacity 0.6s;
    transition: opacity 0.6s;
}

.light-btn {
    color: #fafafa;
    background-color: #333;
    border: solid 3px #777;
    padding: 5px 15px;
    border-radius: 1px;
    text-decoration: none;
    cursor: pointer;
    vertical-align: middle;
    position: absolute;
    top: 45%;
    z-index: 99;
}

.light-btn:hover {
    background-color: #111;
}

.btn-prev {
    left: 7%;
}

.btn-next {
    right: 7%;
}

.btn-close {
    position: absolute;
    right: 2%;
    top: 2%;
    color: #fafafa;
    background-color: #92001d;
    border: solid 5px #ef4036;
    padding: 10px 15px;
    border-radius: 1px;
    text-decoration: none;
}

.btn-close:hover {
    background-color: #740404;
}
  </style>
</head>

<body>
    {{ range $index, $element := .Page.Params.gallery_images }}
    {{ $image := . }}
    <a href="{{ $image }}">
        <img class="thumb" src="{{ $image }}">
    </a>

    <h2></h2>
    <div class="lightbox" id="img1">
        <a href="#img3" class="light-btn btn-prev">prev</a>
        <a href="#_" class="btn-close">X</a>
        <img src="images/velo1.jpg">
        {{ if isset (after $index) }}
            <a href="{{ index .Page.Params.gallery_images (after $index) }}" class="light-btn btn-next">next</a>
        {{ end }}
    </div>

    {{ end }}    
    <p class="footer">Velociraptor bytes!</p>
</body>