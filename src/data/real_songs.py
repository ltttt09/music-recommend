"""Real-world song catalog for the music recommender."""

REAL_SONGS = [
    # Pop
    {"title": "Blinding Lights", "artist": "The Weeknd", "album": "After Hours", "year": 2020, "genre": "Pop", "duration_ms": 200040},
    {"title": "Shape of You", "artist": "Ed Sheeran", "album": "Divide", "year": 2017, "genre": "Pop", "duration_ms": 233713},
    {"title": "Uptown Funk", "artist": "Mark Ronson ft. Bruno Mars", "album": "Uptown Special", "year": 2014, "genre": "Pop", "duration_ms": 270000},
    {"title": "Happy", "artist": "Pharrell Williams", "album": "G I R L", "year": 2013, "genre": "Pop", "duration_ms": 232720},
    {"title": "Rolling in the Deep", "artist": "Adele", "album": "21", "year": 2011, "genre": "Pop", "duration_ms": 228093},
    {"title": "Shake It Off", "artist": "Taylor Swift", "album": "1989", "year": 2014, "genre": "Pop", "duration_ms": 219200},
    {"title": "Levitating", "artist": "Dua Lipa", "album": "Future Nostalgia", "year": 2020, "genre": "Pop", "duration_ms": 203808},
    {"title": "Watermelon Sugar", "artist": "Harry Styles", "album": "Fine Line", "year": 2019, "genre": "Pop", "duration_ms": 174000},
    {"title": "Bad Guy", "artist": "Billie Eilish", "album": "When We All Fall Asleep", "year": 2019, "genre": "Pop", "duration_ms": 194000},
    {"title": "Circles", "artist": "Post Malone", "album": "Hollywood's Bleeding", "year": 2019, "genre": "Pop", "duration_ms": 215000},
    {"title": "Someone Like You", "artist": "Adele", "album": "21", "year": 2011, "genre": "Pop", "duration_ms": 285000},
    {"title": "Perfect", "artist": "Ed Sheeran", "album": "Divide", "year": 2017, "genre": "Pop", "duration_ms": 263000},
    {"title": "Dance Monkey", "artist": "Tones and I", "album": "The Kids Are Coming", "year": 2019, "genre": "Pop", "duration_ms": 209000},
    {"title": "Senorita", "artist": "Shawn Mendes & Camila Cabello", "album": "Senorita", "year": 2019, "genre": "Pop", "duration_ms": 191000},
    {"title": "Don't Start Now", "artist": "Dua Lipa", "album": "Future Nostalgia", "year": 2019, "genre": "Pop", "duration_ms": 183000},

    # Rock
    {"title": "Bohemian Rhapsody", "artist": "Queen", "album": "A Night at the Opera", "year": 1975, "genre": "Rock", "duration_ms": 355000},
    {"title": "Stairway to Heaven", "artist": "Led Zeppelin", "album": "Led Zeppelin IV", "year": 1971, "genre": "Rock", "duration_ms": 482000},
    {"title": "Hotel California", "artist": "Eagles", "album": "Hotel California", "year": 1977, "genre": "Rock", "duration_ms": 391000},
    {"title": "Sweet Child O' Mine", "artist": "Guns N' Roses", "album": "Appetite for Destruction", "year": 1987, "genre": "Rock", "duration_ms": 356000},
    {"title": "Smells Like Teen Spirit", "artist": "Nirvana", "album": "Nevermind", "year": 1991, "genre": "Rock", "duration_ms": 301000},
    {"title": "Back in Black", "artist": "AC/DC", "album": "Back in Black", "year": 1980, "genre": "Rock", "duration_ms": 255000},
    {"title": "Wonderwall", "artist": "Oasis", "album": "What's the Story Morning Glory", "year": 1995, "genre": "Rock", "duration_ms": 258000},
    {"title": "Come As You Are", "artist": "Nirvana", "album": "Nevermind", "year": 1991, "genre": "Rock", "duration_ms": 219000},
    {"title": "Californication", "artist": "Red Hot Chili Peppers", "album": "Californication", "year": 1999, "genre": "Rock", "duration_ms": 321000},
    {"title": "Paint It Black", "artist": "The Rolling Stones", "album": "Aftermath", "year": 1966, "genre": "Rock", "duration_ms": 225000},
    {"title": "Highway to Hell", "artist": "AC/DC", "album": "Highway to Hell", "year": 1979, "genre": "Rock", "duration_ms": 208000},
    {"title": "Dream On", "artist": "Aerosmith", "album": "Aerosmith", "year": 1973, "genre": "Rock", "duration_ms": 266000},

    # Hip-Hop
    {"title": "Lose Yourself", "artist": "Eminem", "album": "8 Mile Soundtrack", "year": 2002, "genre": "Hip-Hop", "duration_ms": 320000},
    {"title": "HUMBLE.", "artist": "Kendrick Lamar", "album": "DAMN.", "year": 2017, "genre": "Hip-Hop", "duration_ms": 177000},
    {"title": "God's Plan", "artist": "Drake", "album": "Scorpion", "year": 2018, "genre": "Hip-Hop", "duration_ms": 199000},
    {"title": "Sicko Mode", "artist": "Travis Scott", "album": "Astroworld", "year": 2018, "genre": "Hip-Hop", "duration_ms": 312000},
    {"title": "Old Town Road", "artist": "Lil Nas X", "album": "7", "year": 2019, "genre": "Hip-Hop", "duration_ms": 157000},
    {"title": "Hotline Bling", "artist": "Drake", "album": "Views", "year": 2015, "genre": "Hip-Hop", "duration_ms": 267000},
    {"title": "Juicy", "artist": "The Notorious B.I.G.", "album": "Ready to Die", "year": 1994, "genre": "Hip-Hop", "duration_ms": 320000},
    {"title": "Stan", "artist": "Eminem ft. Dido", "album": "The Marshall Mathers LP", "year": 2000, "genre": "Hip-Hop", "duration_ms": 404000},

    # Electronic
    {"title": "Get Lucky", "artist": "Daft Punk ft. Pharrell", "album": "Random Access Memories", "year": 2013, "genre": "Electronic", "duration_ms": 369000},
    {"title": "Strobe", "artist": "Deadmau5", "album": "For Lack of a Better Name", "year": 2009, "genre": "Electronic", "duration_ms": 637000},
    {"title": "Levels", "artist": "Avicii", "album": "True", "year": 2011, "genre": "Electronic", "duration_ms": 202000},
    {"title": "Clarity", "artist": "Zedd ft. Foxes", "album": "Clarity", "year": 2012, "genre": "Electronic", "duration_ms": 271000},
    {"title": "Wake Me Up", "artist": "Avicii", "album": "True", "year": 2013, "genre": "Electronic", "duration_ms": 247000},
    {"title": "Titanium", "artist": "David Guetta ft. Sia", "album": "Nothing but the Beat", "year": 2011, "genre": "Electronic", "duration_ms": 245000},

    # R&B
    {"title": "Thinking Out Loud", "artist": "Ed Sheeran", "album": "x", "year": 2014, "genre": "R&B", "duration_ms": 281000},
    {"title": "All of Me", "artist": "John Legend", "album": "Love in the Future", "year": 2013, "genre": "R&B", "duration_ms": 269000},
    {"title": "No Diggity", "artist": "Blackstreet ft. Dr. Dre", "album": "Another Level", "year": 1996, "genre": "R&B", "duration_ms": 311000},
    {"title": "Ordinary People", "artist": "John Legend", "album": "Get Lifted", "year": 2004, "genre": "R&B", "duration_ms": 280000},
    {"title": "Adorn", "artist": "Miguel", "album": "Kaleidoscope Dream", "year": 2012, "genre": "R&B", "duration_ms": 193000},

    # Jazz
    {"title": "Take Five", "artist": "Dave Brubeck", "album": "Time Out", "year": 1959, "genre": "Jazz", "duration_ms": 324000},
    {"title": "So What", "artist": "Miles Davis", "album": "Kind of Blue", "year": 1959, "genre": "Jazz", "duration_ms": 562000},
    {"title": "My Funny Valentine", "artist": "Chet Baker", "album": "Chet Baker Sings", "year": 1954, "genre": "Jazz", "duration_ms": 155000},
    {"title": "Fly Me to the Moon", "artist": "Frank Sinatra", "album": "It Might as Well Be Swing", "year": 1964, "genre": "Jazz", "duration_ms": 150000},

    # Classical
    {"title": "Clair de Lune", "artist": "Claude Debussy", "album": "Suite Bergamasque", "year": 1905, "genre": "Classical", "duration_ms": 300000},
    {"title": "The Four Seasons: Spring", "artist": "Antonio Vivaldi", "album": "The Four Seasons", "year": 1725, "genre": "Classical", "duration_ms": 200000},
    {"title": "Canon in D", "artist": "Johann Pachelbel", "album": "Canon and Gigue", "year": 1680, "genre": "Classical", "duration_ms": 360000},
    {"title": "Moonlight Sonata", "artist": "Ludwig van Beethoven", "album": "Piano Sonata No. 14", "year": 1801, "genre": "Classical", "duration_ms": 360000},

    # Country
    {"title": "Jolene", "artist": "Dolly Parton", "album": "Jolene", "year": 1973, "genre": "Country", "duration_ms": 162000},
    {"title": "Take Me Home, Country Roads", "artist": "John Denver", "album": "Poems, Prayers & Promises", "year": 1971, "genre": "Country", "duration_ms": 192000},
    {"title": "Ring of Fire", "artist": "Johnny Cash", "album": "Ring of Fire", "year": 1963, "genre": "Country", "duration_ms": 157000},
    {"title": "The Gambler", "artist": "Kenny Rogers", "album": "The Gambler", "year": 1978, "genre": "Country", "duration_ms": 212000},

    # Metal
    {"title": "Enter Sandman", "artist": "Metallica", "album": "Metallica", "year": 1991, "genre": "Metal", "duration_ms": 331000},
    {"title": "Paranoid", "artist": "Black Sabbath", "album": "Paranoid", "year": 1970, "genre": "Metal", "duration_ms": 173000},
    {"title": "Master of Puppets", "artist": "Metallica", "album": "Master of Puppets", "year": 1986, "genre": "Metal", "duration_ms": 515000},
    {"title": "Ace of Spades", "artist": "Motorhead", "album": "Ace of Spades", "year": 1980, "genre": "Metal", "duration_ms": 168000},

    # Latin
    {"title": "Despacito", "artist": "Luis Fonsi ft. Daddy Yankee", "album": "Vida", "year": 2017, "genre": "Latin", "duration_ms": 229000},
    {"title": "Hips Don't Lie", "artist": "Shakira ft. Wyclef Jean", "album": "Oral Fixation Vol. 2", "year": 2006, "genre": "Latin", "duration_ms": 218000},
    {"title": "Bailando", "artist": "Enrique Iglesias", "album": "Sex and Love", "year": 2014, "genre": "Latin", "duration_ms": 243000},
    {"title": "Mi Gente", "artist": "J Balvin & Willy William", "album": "Mi Gente", "year": 2017, "genre": "Latin", "duration_ms": 189000},

    # Folk
    {"title": "The Sound of Silence", "artist": "Simon & Garfunkel", "album": "Sounds of Silence", "year": 1965, "genre": "Folk", "duration_ms": 185000},
    {"title": "Blowin' in the Wind", "artist": "Bob Dylan", "album": "The Freewheelin' Bob Dylan", "year": 1963, "genre": "Folk", "duration_ms": 168000},
    {"title": "Hallelujah", "artist": "Leonard Cohen", "album": "Various Positions", "year": 1984, "genre": "Folk", "duration_ms": 279000},

    # More variety
    {"title": "Summertime Sadness", "artist": "Lana Del Rey", "album": "Born to Die", "year": 2012, "genre": "Pop", "duration_ms": 265000},
    {"title": "Radioactive", "artist": "Imagine Dragons", "album": "Night Visions", "year": 2012, "genre": "Rock", "duration_ms": 187000},
    {"title": "Counting Stars", "artist": "OneRepublic", "album": "Native", "year": 2013, "genre": "Pop", "duration_ms": 257000},
    {"title": "Royals", "artist": "Lorde", "album": "Pure Heroine", "year": 2013, "genre": "Pop", "duration_ms": 190000},
    {"title": "Somebody That I Used to Know", "artist": "Gotye ft. Kimbra", "album": "Making Mirrors", "year": 2011, "genre": "Pop", "duration_ms": 244000},
    {"title": "Poker Face", "artist": "Lady Gaga", "album": "The Fame", "year": 2008, "genre": "Pop", "duration_ms": 237000},
    {"title": "Billie Jean", "artist": "Michael Jackson", "album": "Thriller", "year": 1983, "genre": "Pop", "duration_ms": 294000},
    {"title": "Purple Rain", "artist": "Prince", "album": "Purple Rain", "year": 1984, "genre": "Rock", "duration_ms": 521000},
    {"title": "Like a Rolling Stone", "artist": "Bob Dylan", "album": "Highway 61 Revisited", "year": 1965, "genre": "Rock", "duration_ms": 373000},
    {"title": "Yesterday", "artist": "The Beatles", "album": "Help!", "year": 1965, "genre": "Rock", "duration_ms": 125000},
    {"title": "Hey Jude", "artist": "The Beatles", "album": "Hey Jude", "year": 1968, "genre": "Rock", "duration_ms": 431000},
    {"title": "Let It Be", "artist": "The Beatles", "album": "Let It Be", "year": 1970, "genre": "Rock", "duration_ms": 243000},
    {"title": "Imagine", "artist": "John Lennon", "album": "Imagine", "year": 1971, "genre": "Rock", "duration_ms": 187000},
    {"title": "Wish You Were Here", "artist": "Pink Floyd", "album": "Wish You Were Here", "year": 1975, "genre": "Rock", "duration_ms": 334000},
    {"title": "Comfortably Numb", "artist": "Pink Floyd", "album": "The Wall", "year": 1979, "genre": "Rock", "duration_ms": 384000},
    {"title": "Thunderstruck", "artist": "AC/DC", "album": "The Razors Edge", "year": 1990, "genre": "Rock", "duration_ms": 292000},
    {"title": "Livin' on a Prayer", "artist": "Bon Jovi", "album": "Slippery When Wet", "year": 1986, "genre": "Rock", "duration_ms": 249000},
    {"title": "Don't Stop Believin'", "artist": "Journey", "album": "Escape", "year": 1981, "genre": "Rock", "duration_ms": 251000},
    {"title": "Africa", "artist": "Toto", "album": "Toto IV", "year": 1982, "genre": "Rock", "duration_ms": 295000},
    {"title": "Everybody Wants to Rule the World", "artist": "Tears for Fears", "album": "Songs from the Big Chair", "year": 1985, "genre": "Pop", "duration_ms": 251000},
    {"title": "Take On Me", "artist": "a-ha", "album": "Hunting High and Low", "year": 1985, "genre": "Pop", "duration_ms": 228000},
    {"title": "Sweet Dreams", "artist": "Eurythmics", "album": "Sweet Dreams", "year": 1983, "genre": "Pop", "duration_ms": 216000},
    {"title": "Girls Just Want to Have Fun", "artist": "Cyndi Lauper", "album": "She's So Unusual", "year": 1983, "genre": "Pop", "duration_ms": 235000},
    {"title": "Like a Prayer", "artist": "Madonna", "album": "Like a Prayer", "year": 1989, "genre": "Pop", "duration_ms": 340000},
    {"title": "I Wanna Dance with Somebody", "artist": "Whitney Houston", "album": "Whitney", "year": 1987, "genre": "Pop", "duration_ms": 291000},
    {"title": "Careless Whisper", "artist": "George Michael", "album": "Make It Big", "year": 1984, "genre": "Pop", "duration_ms": 304000},
    {"title": "Every Breath You Take", "artist": "The Police", "album": "Synchronicity", "year": 1983, "genre": "Rock", "duration_ms": 253000},
    {"title": "Another Brick in the Wall", "artist": "Pink Floyd", "album": "The Wall", "year": 1979, "genre": "Rock", "duration_ms": 233000},
    {"title": "Riders on the Storm", "artist": "The Doors", "album": "L.A. Woman", "year": 1971, "genre": "Rock", "duration_ms": 434000},
    {"title": "Light My Fire", "artist": "The Doors", "album": "The Doors", "year": 1967, "genre": "Rock", "duration_ms": 427000},
    {"title": "Kashmir", "artist": "Led Zeppelin", "album": "Physical Graffiti", "year": 1975, "genre": "Rock", "duration_ms": 508000},
    {"title": "Whole Lotta Love", "artist": "Led Zeppelin", "album": "Led Zeppelin II", "year": 1969, "genre": "Rock", "duration_ms": 333000},
    {"title": "Thriller", "artist": "Michael Jackson", "album": "Thriller", "year": 1983, "genre": "Pop", "duration_ms": 358000},
    {"title": "Beat It", "artist": "Michael Jackson", "album": "Thriller", "year": 1983, "genre": "Pop", "duration_ms": 258000},
    {"title": "Smooth Criminal", "artist": "Michael Jackson", "album": "Bad", "year": 1987, "genre": "Pop", "duration_ms": 258000},
    {"title": "Rock with You", "artist": "Michael Jackson", "album": "Off the Wall", "year": 1979, "genre": "Pop", "duration_ms": 220000},
    {"title": "Superstition", "artist": "Stevie Wonder", "album": "Talking Book", "year": 1972, "genre": "R&B", "duration_ms": 246000},
    {"title": "What's Going On", "artist": "Marvin Gaye", "album": "What's Going On", "year": 1971, "genre": "R&B", "duration_ms": 233000},
    {"title": "Respect", "artist": "Aretha Franklin", "album": "I Never Loved a Man", "year": 1967, "genre": "R&B", "duration_ms": 148000},
    {"title": "Ain't No Sunshine", "artist": "Bill Withers", "album": "Just As I Am", "year": 1971, "genre": "R&B", "duration_ms": 125000},
    {"title": "Let's Stay Together", "artist": "Al Green", "album": "Let's Stay Together", "year": 1971, "genre": "R&B", "duration_ms": 198000},
    {"title": "Killing Me Softly", "artist": "Fugees", "album": "The Score", "year": 1996, "genre": "Hip-Hop", "duration_ms": 299000},
    {"title": "California Love", "artist": "2Pac ft. Dr. Dre", "album": "All Eyez on Me", "year": 1995, "genre": "Hip-Hop", "duration_ms": 301000},
    {"title": "Nuthin' But a G Thang", "artist": "Dr. Dre ft. Snoop Dogg", "album": "The Chronic", "year": 1992, "genre": "Hip-Hop", "duration_ms": 238000},
    {"title": "The Message", "artist": "Grandmaster Flash", "album": "The Message", "year": 1982, "genre": "Hip-Hop", "duration_ms": 454000},

    # More recent
    {"title": "Flowers", "artist": "Miley Cyrus", "album": "Endless Summer Vacation", "year": 2023, "genre": "Pop", "duration_ms": 200000},
    {"title": "As It Was", "artist": "Harry Styles", "album": "Harry's House", "year": 2022, "genre": "Pop", "duration_ms": 166000},
    {"title": "Anti-Hero", "artist": "Taylor Swift", "album": "Midnights", "year": 2022, "genre": "Pop", "duration_ms": 200000},
    {"title": "Good 4 U", "artist": "Olivia Rodrigo", "album": "SOUR", "year": 2021, "genre": "Pop", "duration_ms": 178000},
    {"title": "Drivers License", "artist": "Olivia Rodrigo", "album": "SOUR", "year": 2021, "genre": "Pop", "duration_ms": 242000},
    {"title": "Stay", "artist": "The Kid LAROI & Justin Bieber", "album": "F*CK LOVE 3+", "year": 2021, "genre": "Pop", "duration_ms": 141000},
    {"title": "Montero", "artist": "Lil Nas X", "album": "Montero", "year": 2021, "genre": "Pop", "duration_ms": 138000},
    {"title": "Peaches", "artist": "Justin Bieber", "album": "Justice", "year": 2021, "genre": "Pop", "duration_ms": 198000},
    {"title": "Save Your Tears", "artist": "The Weeknd", "album": "After Hours", "year": 2020, "genre": "Pop", "duration_ms": 216000},
    {"title": "Sunflower", "artist": "Post Malone & Swae Lee", "album": "Spider-Man: Into the Spider-Verse", "year": 2018, "genre": "Hip-Hop", "duration_ms": 158000},
    {"title": "Rockstar", "artist": "Post Malone ft. 21 Savage", "album": "Beerbongs & Bentleys", "year": 2017, "genre": "Hip-Hop", "duration_ms": 218000},
    {"title": "Congratulations", "artist": "Post Malone", "album": "Stoney", "year": 2016, "genre": "Hip-Hop", "duration_ms": 220000},
    {"title": "Better Now", "artist": "Post Malone", "album": "Beerbongs & Bentleys", "year": 2018, "genre": "Hip-Hop", "duration_ms": 231000},
]

# Total: ~120 songs across all genres
