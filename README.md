# Requiem Ambassador

The goal of the ambassador is to secure the game client from little known severe security vulnerabilities by providing an HTTP reverse proxy that will scan every SWF requested by the game client and block content that is out of the usual for the simple asset files that are supposed to be loaded over the network at runtime in the game. The way that some content in the game is loaded has the implication that one file replaced on the content servers (cdn/other) can result in **severe** damage due to the code in those SWFs have filesystem access, and existing XSS vulnerabilities that were once used had the capability to be used for much more than session hijacking. The primary aim of the ambassador is to provide a client side security guarantee for users of private servers on the game.

## Bundling the Ambassador

The ambassador is meant to be shipped along-side a modified version of the original downloadable desktop client swf. To cut a long story short: The original game client SWF can be taken, a new adobe/harmon air captive runtime can be made for it automatically, and the ambassador can be shipped alongside it, all of this can be achieved in one of the following commands, and our experimentation code [can be seen for better context here](https://github.com/RequiemWorld/requiem_experiments/tree/main/actionscript_to_captive_runtime_02)
### Pre-requisites - Java/The AIR sdk bin directory must be in the system path
- The AIR sdk must be in the systems path so that the application can locate it and use the ADT utility.
- The version of AIR that should be used to build it should be the one in the path.
- This has been gotten to this point with version 51.1.3
### Example Command - Usage - New Distribution of original game SWF with ambassador.
``
invoke bundle-ambassador-and-client-windows-zip C:\Users\<redacted>\Downloads\game\the_swf_name_here.swf C:\Users\<redacted>\Documents\requiem_ambassador
``
### Example Command - Result - Resulting Structure
```
requiem_ambassador/
├── ambassador_prototyping.cfg
├── ambassador_prototyping.exe
└── requiem-restore
    ├── Adobe AIR
    │   └── Versions
    │       └── 1.0
    │           ├── Adobe AIR.dll
    │           ├── Adobe AIR.dll:Zone.Identifier:$DATA
    │           └── Resources
    │               ├── Adobe AIR.vch
    │               ├── Adobe AIR.vch:Zone.Identifier:$DATA
    │               ├── adobecp.vch
    │               ├── adobecp.vch:Zone.Identifier:$DATA
    │               ├── CaptiveAppEntry.exe
    │               ├── CaptiveAppEntry.exe:Zone.Identifier:$DATA
    │               ├── CaptiveCmdEntry.exe
    │               ├── CaptiveCmdEntry.exe:Zone.Identifier:$DATA
    │               └── Licenses
    │                   ├── cairo
    │                   │   ├── COPYING
    │                   │   ├── COPYING-LGPL-2.1
    │                   │   ├── COPYING-LGPL-2.1:Zone.Identifier:$DATA
    │                   │   ├── COPYING-MPL-1.1
    │                   │   ├── COPYING-MPL-1.1:Zone.Identifier:$DATA
    │                   │   └── COPYING:Zone.Identifier:$DATA
    │                   ├── pcre2
    │                   │   ├── COPYING
    │                   │   └── COPYING:Zone.Identifier:$DATA
    │                   └── pixman
    │                       ├── COPYING
    │                       └── COPYING:Zone.Identifier:$DATA
    ├── application.swf
    ├── data
    │   └── config.xml
    ├── META-INF
    │   ├── AIR
    │   │   ├── application.xml
    │   │   └── hash
    │   └── signatures.xml
    ├── mimetype
    └── RequiemRestore.exe
```

## Content Loading Vulnerability

Content on the original game client is loaded into the same context/security sandbox as the main application. This appears to be necessary for how some of the content like the dance planet is loaded at runtime, it has access to all of the code and same context of the main application (all singletons for context), and in the case of running on adobe/harmon air this has major implications, such that the main SWF file on air is in a special sandbox with less restrictions and more access, content loaded into it has access to the filesystem and unrestricted networking access (no policy checks). The issue goes further due to content like clothing and throwables being loaded into the game client this way. **This is to put short:** Various XSS incidents on the game allowed for and had stuff happen that shouldn't have been possible, like closing the game client (something only the main application can do), access to shared objects (flash cookies), and more. This issue was never exploited beyond gaining access to accounts on the game, and I don't believe that [insert company name here] were aware of it, there were several other incidents prior to shutdown that could have been enough.

- The content loading vulnerability means that if one SWF file is added to or replaced on the servers then any person on the game can be silently compromised with filesystem/networking access.
- The content loading vulnerability means that when there is an XSS vulnerability it isn't as harmless as JavaScript being executed in your browser, it can mean that in certain incidents (with throwables specifically) it is severe damage possible, officially, 100% of the time. Cross-Site Scripting is not good in the browser but the difference is that your browser has to be vulnerable usually for it to be a problem effecting more than the platform (some caveats).

## HTTP Proxy/SWF Filter

- The ambassadors http reverse proxy will decompress (where applicable (CWS, ZWS variants) SWFs in responses from upstream servers and scan them for their usage of anything that could be used to cause damage that wouldn't be in any of the item assets. [IMPLEMENTATION IN PROGRESS]
- The ambassadors http reverse proxy will assure that stuff specific to http/proxying doesn't interfere with scanning/blocking SWF content. The Transfer-Encoding and Content-Encoding headers will be removed if they are present in the response from a remote server for a SWF, this prevents the risk that we can receive a SWF in an encoded response, see it as other harmless binary data, send it to the client with the content-encoding or transfer-encoding header, and that the client may decode the SWF and execute it like normal, allowing for severe damage to be possible again. 

## Game Proxy/Filtering

- The ambassadors game reverse proxy will assure that only packet (packet in the sense of layer 7 custom protocol) types that we are confident can not be used to make the client load content from whole URLs that would not be scanned by the SWF filtering solution on our reverse proxy.
  - Different packets for different purposes from the game server are designated different numbers to indicate what to expect ahead. This will be put on a whitelist so that only safe packets are allowed to reach the client. 99% of the ones that I am personally aware of tell the client the relative path of something to load to combine with a CDN url acquired at startup to form a flow such as: packet (with /i/item/path somewhere) -> client -> ``cdn-url.example.com/i/item/path/item.xml``.

## Architecture/Testing
- The core logic for taking an HTTP request, getting a response and scanning/filtering it is built using ports & adapters architecture, and the logic for filtering responses is being fully tested at the unit level to assure that when HTTP api/client libraries change, the core request making/secure response giving logic will remain the same and working.
  - Some of our code has adapter level integration tests using wiremock to assure that they work enough as intended individually. 

## End Goal/Progress

The end goal of the ambasasdor is to allow us to get the client operational safely again and to provide the solution to the community for play on any private server safely should the opportunity arise. In the current state. This should not be considered ready or safe beyond what we are releasing on this project, as it is not ready to shield unpatched clients from known XSS vulnerabilities, that is to say that the throw XSS vulnerability will be patched on our modified client, and a whole URL in the packet would be unable to get past the ambassador, but given an unpatched client the packet with the whole URL will not be dropped in the current state. This application is built with at least 75% of the architecture/testing capability of the Requiem World project. The end goal will be to add a suite of acceptance tests to smooth further development and make it easier to expand on this application as a whole in the future.