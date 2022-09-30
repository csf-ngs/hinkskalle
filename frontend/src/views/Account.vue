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
        <v-col cols="12" md="8" offset-md="2">
          <h4>Registered Security Keys</h4>
        </v-col>
      </v-row>
      <v-row>
        <v-col v-for="passkey in passkeys" :key="passkey.id" cols="12" md="8" offset-md="2">
          <v-card color="blue-grey lighten-5" hover raised>
            <v-card-title class="text-h6">
              {{passkey.name}}
            </v-card-title>
            <v-divider></v-divider>
            <v-list dense>
              <v-list-item two-line>
                <v-list-item-content>
                  <v-list-item-title class="d-flex justify-space-between">
                    <div style="width:33%">
                      {{passkey.createdAt | prettyDateTime}}
                    </div>
                    <div style="width:33%" class="text-center">
                      {{passkeys.last_used ? (passkey.last_used | prettyDateTime) : '-'}}
                    </div>
                    <div style="width:33%" class="text-right">
                      {{passkey.login_count}}
                    </div>
                  </v-list-item-title>
                  <v-list-item-subtitle class="d-flex justify-space-between">
                    <div style="width:33%">Created</div>
                    <div style="width:33%" class="text-center">Last Used</div>
                    <div style="width:33%" class="text-right"># Used</div>
                  </v-list-item-subtitle>
                </v-list-item-content>
                <v-list-item-action>
                  <v-btn icon @click="deletePasskey(passkey)">
                    <v-icon small color="red lighten-1">mdi-delete</v-icon>
                  </v-btn>
                </v-list-item-action>
              </v-list-item>
            </v-list>
          </v-card>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="8" md="5" offset-md="3">
          <v-text-field
            type="text"
            outlined
            v-model="localState.newCredentialName"
            label="Name your Key"
            ></v-text-field>
        </v-col>
        <v-col cols="4" md="1">
          <v-btn @click="createKey()" :disabled="!newCredentialValid">Test Credential!</v-btn>
        </v-col>
      </v-row>
    </v-container>
    
  </div>
</template>
<script lang="ts">
import Vue from 'vue';
import { User, PassKey } from '../store/models';

import { clone as _clone } from 'lodash';

import { b64url_encode } from '@/util/b64url';

interface State {
  editUser: User | null;
  editValid: boolean;
  showPwChange: boolean;
  oldPassword: string;
  password1: string;
  password2: string;
  pwChangeValid: boolean;
  newCredentialName: string;
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
      newCredentialName: '',
    },
  }),
  mounted: function() {
    this.localState.editUser = _clone(this.$store.getters.currentUser);
    this.loadPasskeys();
  },
  computed: {
    passwordsMatching(): boolean {
      return this.localState.password1 != '' && this.localState.password2 != '' &&
        this.localState.password1 === this.localState.password2;
    },
    oldPasswordMissing(): boolean {
      return !this.localState.oldPassword;
    },
    newCredentialValid(): boolean {
      return this.localState.newCredentialName != '';
    },
    passkeys(): PassKey[] {
      return this.$store.getters['passkeys/list'];
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
    loadPasskeys(): Promise<PassKey[]> {
      return this.$store.dispatch('passkeys/list')
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    deletePasskey(key: PassKey): Promise<void> {
      return this.$store.dispatch('passkeys/delete', key)
        .then(() => this.$store.commit('snackbar/showSuccess', 'Is gone.') )
        .catch(err => this.$store.commit('snackbar/showError', err))
    },
    createKey() {
      this.$store.dispatch('getAuthnCreateOptions')
        // eslint-disable-next-line
        .then((createOptions: CredentialCreationOptions) => {
          navigator.credentials.create(createOptions).then(
            (cred) => {
              if (!cred) return;
              const validOrigin: string = this.$store.getters.config.frontend_url;
              const cdj = JSON.parse(new TextDecoder().decode((cred as any).response.clientDataJSON));
              if (cdj.type != 'webauthn.create' || 
                    (('crossOrigin' in cdj) && cdj.crossOrigin) ||
                    !validOrigin.startsWith(cdj.origin)) {

                console.log("cdj invalid", cdj);
                this.$store.commit('snackbar/showError', 'Could not validate credentials.');
                return;
              }
              const postData = {
                name: this.localState.newCredentialName,
                authenticator_data: b64url_encode((cred as any).response.getAuthenticatorData()),
                public_key: b64url_encode((cred as any).response.getPublicKey()),
                cdj: cdj,
              };
              console.log(postData);
              this.$store.dispatch('registerCredential', postData)
                .then((key: PassKey) => {
                  console.log(key);
                  this.$store.commit('snackbar/showSuccess', 'Key created');
                })
                .catch(err => {
                  this.$store.commit('snackbar/showError', err);
                })
            },
            (err: Error) => {
              console.error(err);
              this.$store.commit('snackbar/showError', "Failed to get credentials.");
            }
          );
        })
      .catch(err => {
        this.$store.commit('snackbar/showError', err);
      });
    }
  }
});
</script>