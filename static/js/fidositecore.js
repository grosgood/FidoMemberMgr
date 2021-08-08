// fidositecore - JavaScript to load into client browsers
// visiting the FIDO Membership Manager site

function startWizardWindow(initurl) {
  // make a minimalist start page. initurl is the first page of a
  // wizard sequence
  var wizwindow = window.open(initurl, "FIDOWizard", "width=520,height=320,toolbar=0,location=0,directories=0,status=0,menubar=0,scrollbars=1,resizable=1");
  if (wizwindow == null) {
    window.alert("Could not launch a wizard.");
  }
}

function wizardCancel(gtourl) {
  // Put up an 'are you sure? alert box, and if they're sure, close
  // down the wizard window.
  flag = window.confirm("Canceling member entry. 'OK', closes wizard; you may complete the entry later. 'Cancel' will 'cancel the cancellation'.");
  if (flag == true)  {
    window.opener.top.location = gtourl
    window.close();
  }
}
