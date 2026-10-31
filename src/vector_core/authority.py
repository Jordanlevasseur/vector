"""Decision boundary, not owner authentication or a privileged phrase recognizer."""

class DecisionAuthority:
    def ordinary(self,approved):
        if approved is not True:raise PermissionError('Explicit control-channel approval required.')
        return {'authority':'ordinary explicit user control; not authenticated privileged override'}

    def privileged_override(self,*args,**kwargs):
        raise PermissionError('Privileged owner override unavailable: authentication is not designed or authorized.')
