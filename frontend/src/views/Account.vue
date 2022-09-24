<template>
  <div class="account">
    <top-bar title="Account"></top-bar>
    <v-container>
      <v-row v-if="localState.editUser">
        <v-col cols="12" md="8" offset-md="2">
          <v-form v-model="localState.editValid">
            <v-container>
              <v-row>
                <v-col cols="12" md="6">
                  <hsk-text-input id="firstname" 
                    label="Firstname"
                    field="firstname"
                    :obj="localState.editUser"
                    :readonly="localState.editUser.source!='local'"
                    required
                    @updated="localState.editUser=$event"></hsk-text-input>
                </v-col>
                <v-col cols="12" md="6">
                  <hsk-text-input id="lastname" 
                    label="Lastname"
                    field="lastname"
                    :obj="localState.editUser"
                    :readonly="localState.editUser.source!='local'"
                    required
                    @updated="localState.editUser=$event"></hsk-text-input>
                </v-col>
                <v-col cols="12" md="6">
                  <hsk-text-input id="username" 
                    :static-value="localState.editUser.username"
                    label="Username"></hsk-text-input>
                </v-col>
                <v-col cols="12" md="6">
                  <hsk-text-input id="email" 
                    label="Email"
                    field="email"
                    :obj="localState.editUser"
                    :readonly="localState.editUser.source!='local'"
                    required
                    @updated="localState.editUser=$event"></hsk-text-input>
                </v-col>
              </v-row>
              <v-row>
                <v-col cols="12">
                  <v-spacer></v-spacer>
                  <v-dialog v-model="localState.showPwChange" max-width="500px">
                    <template v-slot:activator="{ on, attrs }">
                      <v-btn text v-bind="attrs" v-on="on">
                        <v-icon>mdi-shield-key</v-icon> Change Password
                      </v-btn>
                    </template>
                    <v-card>
                      <v-card-title class="headline">Change Password</v-card-title>
                      <v-card-text>
                        <v-container>
                          <v-form v-model="localState.pwChangeValid">
                            <v-row>
                              <v-col cols="12">
                                <v-text-field
                                  :type="localState.passwordVisible ? 'text': 'password'"
                                  outlined
                                  v-model="localState.oldPassword"
                                  label="Current Password"
                                  :error="oldPasswordMissing"
                                  :append-icon="localState.passwordVisible ? 'mdi-eye' : 'mdi-eye-off'"
                                  @click:append="localState.passwordVisible=!localState.passwordVisible"
                                  ></v-text-field>
                              </v-col>
                              <v-col cols="12" md="6">
                                <v-text-field
                                  :type="localState.passwordVisible ? 'text': 'password'"
                                  outlined
                                  v-model="localState.password1"
                                  label="Current Password"
                                  :error="!passwordsMatching"
                                  :append-icon="localState.passwordVisible ? 'mdi-eye' : 'mdi-eye-off'"
                                  @click:append="localState.passwordVisible=!localState.passwordVisible"
                                  ></v-text-field>
                              </v-col>
                              <v-col cols="12" md="6">
                                <v-text-field
                                  :type="localState.passwordVisible ? 'text': 'password'"
                                  outlined
                                  v-model="localState.password2"
                                  label="Current Password"
                                  :error="!passwordsMatching"
                                  :append-icon="localState.passwordVisible ? 'mdi-eye' : 'mdi-eye-off'"
                                  @click:append="localState.passwordVisible=!localState.passwordVisible"
                                  ></v-text-field>
                              </v-col>
                            </v-row>
                          </v-form>
                        </v-container>
                      </v-card-text>
                      <v-card-actions>
                        <v-spacer></v-spacer>
                        <v-btn color="secondary accent-1" text @click="closePwChange">Mabye not today.</v-btn>
                        <v-btn color="primary darken-1" :disabled="!localState.pwChangeValid" text @click="changePassword">Update Password</v-btn>
                      </v-card-actions>
                    </v-card>
                  </v-dialog>
                  <v-btn type="reset" color="secondary accent-1" text @click.prevent="reset()">Reset</v-btn>
                  <v-btn type="submit" color="primary darken-1" text :disabled="!localState.editValid" @click.prevent="update()">Save</v-btn>
                </v-col>
              </v-row>
            </v-container>
          </v-form>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <v-btn @click="createKey()">Test Credential!</v-btn>
        </v-col>
      </v-row>
    </v-container>
    
  </div>
</template>
<script lang="ts">
import Vue from 'vue';
import { User } from '../store/models';

import { clone as _clone } from 'lodash';

interface State {
  editUser: User | null;
  editValid: boolean;
  showPwChange: boolean;
  oldPassword: string;
  password1: string;
  password2: string;
  pwChangeValid: boolean;
}

export default Vue.extend({
  name: 'HskAccount',
  data: (): { localState: State } => ({
    localState: {
      editUser: null,
      editValid: true,
      showPwChange: false,
      oldPassword: '',
      password1: '',
      password2: '',
      pwChangeValid: true,
    },
  }),
  mounted: function() {
    this.localState.editUser = _clone(this.$store.getters.currentUser);
  },
  computed: {
    passwordsMatching(): boolean {
      return this.localState.password1 != '' && this.localState.password2 != '' &&
        this.localState.password1 === this.localState.password2;
    },
    oldPasswordMissing(): boolean {
      return !this.localState.oldPassword;
    },
  },
  watch: {
    'localState.showPwChange': function showPwChange(val) {
      if (!val) {
        this.closePwChange();
      }
    },
  },
  methods: {
    reset() {
      this.localState.editUser = _clone(this.$store.getters.currentUser);
    },
    update() {
      this.$store.dispatch('users/update', this.localState.editUser)
        .then(user => {
          this.$store.commit('setUser', user);
          this.localState.editUser = _clone(this.$store.getters.currentUser);
          this.$store.commit('snackbar/showSuccess', "Hooray!");
        })
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    changePassword() {
      const user = _clone(this.$store.getters.currentUser);
      user.oldPassword = this.localState.oldPassword;
      user.password = this.localState.password1;
      this.$store.dispatch('users/update', user)
        .then(user => {
          this.$store.commit('setUser', user);
          this.$store.commit('snackbar/showSuccess', 'Hooray!');
          this.closePwChange();
        })
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    closePwChange() {
      this.localState.showPwChange=false;
      this.localState.oldPassword='';
      this.localState.password1='';
      this.localState.password2='';
    },
    createKey() {
      // eslint-disable-next-line
      const createOptions : CredentialCreationOptions = {
        publicKey: {
          rp: {
            id: 'localhost',
            name: "Hinkskalle",
          },

          user: {
            id: Uint8Array.from(atob('Vg4vHxiHQnPapKRD4+EIcw=='), c => c.charCodeAt(0)),
            name: 'test.hase',
            displayName: "",
          },
          excludeCredentials: [], // XXX
          pubKeyCredParams: [{
            type: "public-key",
            alg: -7
          }, {
            type: "public-key",
            alg: -257
          }],

          challenge: new Uint8Array([0]),

          authenticatorSelection: {
            authenticatorAttachment: "cross-platform",
            userVerification: "discouraged",
            requireResidentKey: false,
          },
          timeout: 180000,
        }
      };
      navigator.credentials.create(createOptions).then(
        (cred) => {
          console.log(cred);
          if (!cred) return;
          const cdj = JSON.parse(new TextDecoder().decode((cred as any).response.clientDataJSON));
          console.log(cdj);
          console.log(btoa(String.fromCharCode(...new Uint8Array((cred as any).response.getAuthenticatorData()))));
          console.log(btoa(String.fromCharCode(...new Uint8Array((cred as any).response.getPublicKey()))));

        },
        (err: Error) => {
          console.error(err);
        }
      );
    }
  }
});
</script>