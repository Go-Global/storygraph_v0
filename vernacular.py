import spacy, neuralcoref


def get_neighboring_tokens(doc, token, radius=2, stop_at_punct=True):
    assert token in doc, "Error, token not found in document"
    token_pos = token.i
    
    left, right = None, None
    
    if stop_at_punct:
        for i in range(1, radius + 1):
#             print(doc[token_pos - i].pos_, doc[token_pos - i].text)
            if not left and doc[token_pos - i].pos_ == 'PUNCT':
                
                left = token_pos - (i - 1)
            if not right and doc[token_pos + i].pos_ == 'PUNCT':
                right = token_pos + (i - 1)
    
    if not left:
        left = token_pos - radius    
    if not right:
        right = token_pos + radius

    left = max(left, 0)
    right = min(right, len(doc))
    return doc[left:right + 1].text
    
def get_local_contexts(doc, tokens, radius=2):
    for token in tokens:
        print(get_neighboring_tokens(doc, token, radius=radius))
        
if __name__ == "__main__":
    summary = """
    A poacher (Danny Trejo) hides from an unknown creature in his boat. While it breaks through the boat and attempts to catch the poacher, he commits suicide by shooting himself to prevent the beast from killing him.

    Meanwhile, while shooting a documentary about a long-lost indigenous tribe known as the Shirishamas on the Amazon River, director Terri Flores (Jennifer Lopez) and members of her crew including cameraman and childhood friend Danny Rich (Ice Cube), production manager Denise Kalberg (Kari Wuhrer), Denise's boyfriend and sound engineer Gary Dixon (Owen Wilson), narrator Warren Westridge (Jonathan Hyde), anthropologist Professor Steven Cale (Eric Stoltz), and boat skipper Mateo (Vincent Castellanos) come across stranded Paraguayan snake hunter Paul Serone (Jon Voight) and help him, believing he knows how to find the tribe they are searching for.

    Most of the crew are uncomfortable around Serone, and Cale clashes with him several times in regards to Shirishama lore. Later, while trying to free the boat's propeller from a rope, Cale is stung in the throat by a wasp inside his scuba regulator, which swells up his throat and leaves him unconscious. Serone performs an emergency cricothyrotomy, seemingly saving Cale's life. With that, Serone takes over as commander and captain of the boat and the crew. They are then forced to help him achieve his true goal: hunting down and capturing a giant record-breaking green anaconda he had been tracking.

    Later, Mateo gets lost and is the first victim to be killed by the anaconda, which coils around him before it snaps his neck near the boat where the poacher had been killed. A photograph in an old newspaper reveals that Mateo, Serone, and the unnamed poacher were actually working together as a hunting team to catch animals, including snakes. The others try to find him while Gary works alongside Serone, who promises if they help him find the anaconda, he will help them get out alive.

    Later that night, the anaconda appears and attacks the boat crew. When Serone attempts to capture the snake alive, it coils around Gary and begins to crush him. Terri attempts to save Gary by shooting the anaconda, but Serone knocks the gun out of her hands, allowing the snake to kill and devour Gary. Denise mourns the loss of her boyfriend. The survivors overcome Serone and tie him up for punishment. The next day, the boat becomes stuck at a waterfall, requiring Terri, Danny, and Westridge to enter the water to winch it loose. Denise confronts Serone and attempts to kill him in revenge for Gary's death, but he strangles her to death with his legs before dumping her corpse into the river.

    When the anaconda returns, Westridge distracts the snake enough for Terri and Danny to return to the boat while he ascends the waterfall. Danny and the freed Serone battle, as Westridge is coiled by the anaconda. Before it can kill him, the tree supporting the anaconda breaks, sending the group into the water and waking up Cale in the process. With Westridge killed by the anaconda in the fall, the snake attacks Danny and coils itself around him, only for Terri to shoot it in the head. An enraged Serone attacks Terri, only to be stabbed with a tranquilizer dart by Cale, who soon loses consciousness again. Danny punches the drugged Serone, knocking him into the river.

    However, Terri and Danny are soon captured when Serone catches up to them. He dumps a bucket of monkey blood on them and uses them as bait in an attempt to capture a second, much larger anaconda. The snake soon appears where it begins to coil itself around Terri and Danny and slowly suffocates them. They are caught in a net by Serone, but the snake breaks free. Serone himself tries to flee up a ladder, but the anaconda slinks up after him and brings it down. In time the beast uncoils itself, Serone tries again to flee only for Danny to raise his own net over him, giving the anaconda an opportunity to coil itself around Serone before suffocating him to death. As they are cutting their bonds Terri and Danny watch as the anaconda swallows Serone's body whole.

    Terri retreats to a building and finds a nest full of newborn anacondas, but the snake arrives and after it regurgitates Serone's still twitching corpse, which seems to wink at Terri, it chases her up a smoke stack. Danny traps the anaconda by pinning its tail to the ground with a pickaxe and ignites a fire below the smoke shack which burns the snake. An explosion triggers which sends the burning anaconda flying out of the building and it plunges into the water, causing the snake to sink. As Terri and Danny recuperate on a nearby dock, the anaconda appears one final time. Danny slams a splitting axe into the snake's head, finally killing it.

    Afterwards, Terri and Danny reunite with Cale, who begins to revive on the boat. As the three remaining survivors float downriver, they suddenly locate the natives for whom they were previously searching. They realize that Serone was right and resume filming their documentary.
    """
    nlp = spacy.load("en_core_web_lg")
    doc_test = nlp(summary)
    help_ = [token for token in doc_test if token.text.lower() == "help"]
    get_local_contexts(doc_test, help_)
    # get_neighboring_tokens(doc_test, help_[1], radius=3, stop_at_punct=False)